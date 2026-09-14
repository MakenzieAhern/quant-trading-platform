"""Fail-closed, offline parsing of exactly reconciled issuer risk-warning disclosures."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from datetime import date
from itertools import pairwise
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from scripts.reconcile_sse_cninfo import (
    canonical,
    issuer_subject,
    match,
    publication,
    save,
    sha,
    title_key,
)

VERSION = "sse-cninfo-ordinary-name-v6"
DATE = r"(20\d{2})年(\d{1,2})月(\d{1,2})日"


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def status(name: str) -> str:
    name = name.strip("【】").translate(str.maketrans("\u2217\uff0a\ufe61", "***"))
    if re.match(r"^(?:S)?\*ST", name, re.I):
        return "STAR_ST"
    if re.match(r"^(?:S)?ST", name, re.I):
        return "ST"
    return "NORMAL"


def extract(pages: list[str], record: dict[str, Any]) -> dict[str, Any]:
    """Accept an explicit name change and a labeled or tightly linked effective date."""
    sse = record["sse"]
    prefix_mode = record.get("match_method") == "security+date+exact_subject+issuer_prefix"
    confidence, mirrors = match(sse, record["cninfo"], issuer_prefix=prefix_mode)
    if confidence != "EXACT" or record["match_confidence"] != "EXACT":
        raise ValueError("MATCH_NOT_EXACT")
    issuer_name = sse.get("SECURITY_NAME")
    if not issuer_name and prefix_mode:
        issuer_name = mirrors[0].get("secName")
    if not isinstance(issuer_name, str) or not issuer_name.strip():
        raise ValueError("MISSING_SSE_ISSUER_NAME")
    text = compact("\n".join(pages))
    header = text[:500]
    codes = re.search(r"(?:证券|股票)代码\s*[：:]\s*([\d\s、,，]{6,55})", "\n".join(pages)[:1000])  # noqa: RUF001
    if not codes or sse["SECURITY_CODE"] not in re.findall(r"(?<!\d)\d{6}(?!\d)", codes[1]):
        raise ValueError("WRONG_SECURITY_CODE")
    if compact(issuer_name) not in header:
        raise ValueError("WRONG_ISSUER_NAME")
    if not sse.get("SECURITY_NAME") and not re.search(
        r"(?:证券|股票)(?:简称|名称)[\uff1a:]" + re.escape(compact(issuer_name)), header
    ):
        raise ValueError("CNINFO_NAME_NOT_PDF_HEADER")
    issuer = re.search(r"([\u4e00-\u9fff]{4,}(?:股份有限公司|有限责任公司))", sse["TITLE"])
    if issuer and issuer[1] not in text[:1200]:
        raise ValueError("WRONG_ISSUER_COMPANY")
    if prefix_mode:
        for cn in mirrors:
            subject = issuer_subject(cn["announcementTitle"], sse, cn)
            # Old short names can differ from the issuer prefix printed in metadata.
            # The entire About-clause must still occur in the verified issuer PDF.
            if "关于" in subject:
                subject = subject[subject.index("关于") :]
            if subject not in title_key(text[:1200]):
                raise ValueError("PDF_SUBJECT_METADATA_MISMATCH")
            company = re.match(
                r"[\u4e00-\u9fff]+(?:股份有限公司|有限责任公司)", cn["announcementTitle"]
            )
            if company and company[0] not in text[:1200]:
                raise ValueError("WRONG_CNINFO_ISSUER_COMPANY")
    names = list(
        re.finditer(
            r"(?:股票(?:简称)?|证券简称|简称)[\uff1a:]?将?由?[“\"]([^“”\"\uff1b;]{1,20})[”\"]"
            r"(?:变更|更改|变)为[“\"]([^“”\"\uff1b;]{1,20})[”\"]",
            text,
        )
    )
    names = [
        m
        for m in names
        if m[1] == compact(issuer_name) and text[max(0, m.start() - 2) : m.start()] != "扩位"
    ]
    confirmation = False
    if not names:
        name = re.escape(compact(issuer_name))
        names = list(re.finditer(r"(?:股票|证券)简称仍为[“\"](" + name + r")[”\"]", text))
        confirmation = bool(names)
    pairs = {(m[1], m[1] if confirmation else m[2]) for m in names}
    # A separately labeled ordinary A-share name survives malformed quoted prose.
    labels = list(
        re.finditer(r"(?:实施|撤销)后A股简称为([S*ST\u4e00-\u9fff]{1,12})[\uff0c。\uff1b;]", text)
    )
    labeled = {(compact(issuer_name), m[1]) for m in labels}
    if pairs and labeled and pairs != labeled:
        raise ValueError("CONFLICTING_LABELED_NAME")
    if not pairs and len(labeled) == 1:
        pairs = labeled
        names = labels
    if len(pairs) != 1:
        raise ValueError("NAME_TRANSITION_UNRESOLVED")
    old, new = next(iter(pairs))
    if old != compact(issuer_name):
        raise ValueError("OLD_NAME_NOT_HEADER_IDENTITY")
    # Deliberately narrow: references to old events and unrelated suspension dates are not dates.
    dates = list(
        re.finditer(
            r"(?:撤销|实施|实行)[^。\uff1b;\uff1a:]{0,60}风险警示"
            r"[^。\uff1b;\uff1a:]{0,15}起始日(?:期)?为?[\uff1a:]?" + DATE,
            text,
        )
    )
    dated = {(date(int(m[1]), int(m[2]), int(m[3])).isoformat()) for m in dates}
    if not dates and prefix_mode and not confirmation and not labeled:
        # Older layouts date the exact name-change clause rather than a start-date label.
        # Never use a general publication/suspension date or a date from another sentence.
        dates = list(
            re.finditer(
                r"自?" + DATE + r"起[\uff0c,]?[^。\uff1b;\d]{0,40}?" + re.escape(names[0][0]), text
            )
        )
        dated = {date(int(m[1]), int(m[2]), int(m[3])).isoformat() for m in dates}
        if not dates:
            # A resumed-trading date must directly introduce this exact name change.
            # An unrelated resumption sentence is not an effective-date source.
            dates = list(
                re.finditer(
                    DATE + r"复牌[\uff0c,](?:公司(?:的|A股)?)?" + re.escape(names[0][0]), text
                )
            )
            dated = {date(int(m[1]), int(m[2]), int(m[3])).isoformat() for m in dates}
    if len(dated) != 1:
        raise ValueError("EFFECTIVE_DATE_UNRESOLVED")
    effective = next(iter(dated))
    if effective < sse["SSEDATE"]:
        raise ValueError("RETROSPECTIVE_EVENT_REQUIRES_REVIEW")
    old_status, new_status = status(old), status(new)
    if old_status == new_status and not confirmation:
        raise ValueError("NO_STATUS_TRANSITION")
    if confirmation:
        event_type = "STATUS_CONFIRMATION"
    elif old_status == "NORMAL":
        event_type = "ENTRY"
    elif new_status == "NORMAL":
        event_type = "EXIT"
    else:
        event_type = old_status + "_TO_" + new_status
    support = []
    for item in (names[0], dates[0]):
        offset = item.start()
        page_number = 1
        for page in pages:
            length = len(compact(page))
            if offset < length:
                break
            offset -= length
            page_number += 1
        support.append({"page": page_number, "compact_page_offset": offset, "text": item[0]})
    cn = mirrors[0]
    number = re.search(r"(?:公告编号|编号)\s*[\uff1a:]([^\n]{1,60})", "\n".join(pages)[:1000])
    return {
        "security_id": "CN-A:SSE:" + sse["SECURITY_CODE"],
        "symbol": sse["SECURITY_CODE"],
        "old_status": old_status,
        "status": new_status,
        "event_type": event_type,
        "effective_from": effective,
        "effective_to": None,
        "old_name": old,
        "new_name": new,
        "issuer_company_from_sse_title": issuer[1] if issuer else None,
        "issuer_announcement_number": compact(number[1]) if number else None,
        "sse_announcement_id": sse["ORG_BULLETIN_ID"],
        "sse_title": sse["TITLE"],
        "sse_publication_date": sse["SSEDATE"],
        "sse_metadata_snapshot_sha256": record["sse_metadata_snapshot_sha256"],
        "cninfo_document_url": "https://static.cninfo.com.cn/" + cn["adjunctUrl"],
        "cninfo_document_id": cn["announcementId"],
        "cninfo_publication_date": publication(cn),
        "cninfo_document_sha256": record["cninfo_document_sha256"],
        "match_method": record["match_method"],
        "match_confidence": confidence,
        "parser_version": VERSION,
        "support": support,
    }


def normalize(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = {canonical(e): e for e in events}
    return sorted(
        unique.values(),
        key=lambda e: (
            e["security_id"],
            e["effective_from"],
            e["sse_publication_date"],
            e["sse_announcement_id"],
        ),
    )


def status_on(
    events: list[dict[str, Any]],
    security_id: str,
    day: str,
    exclusions: tuple[tuple[str, str, str], ...] = (),
) -> str:
    """Last known event, not a completeness assertion; unknown is never tradable NORMAL."""
    date.fromisoformat(day)
    if any(s == security_id and start <= day <= end for s, start, end in exclusions):
        return "UNKNOWN"
    eligible = [
        e
        for e in normalize(events)
        if e["security_id"] == security_id
        and max(e["sse_publication_date"], e["cninfo_publication_date"], e["effective_from"]) <= day
    ]
    if not eligible:
        return "UNKNOWN"
    latest = max(e["effective_from"] for e in eligible)
    values = {e["status"] for e in eligible if e["effective_from"] == latest}
    return next(iter(values)) if len(values) == 1 else "UNKNOWN"


def build(root: Path, master: Path, sse_snapshot: Path) -> None:
    records = json.loads((root / "reconciliation.json").read_bytes())
    events = []
    unresolved = []
    for record in records:
        try:
            if record["match_confidence"] != "EXACT":
                raise ValueError(record["match_confidence"])
            cn = record["cninfo"][0]
            path = root / "documents" / (cn["announcementId"] + ".pdf")
            raw = path.read_bytes()
            if sha(raw) != record["cninfo_document_sha256"]:
                raise ValueError("DOCUMENT_CHECKSUM_MISMATCH")
            pages = [p.extract_text() for p in PdfReader(io.BytesIO(raw)).pages]
            save(root / "text" / (cn["announcementId"] + ".json"), pages)
            event = extract(pages, record)
            event["retrieved_at_utc"] = json.loads(path.with_suffix(".pdf.meta.json").read_bytes())[
                "retrieved_at_utc"
            ]
            events.append(event)
        except ValueError as exc:
            unresolved.append(
                {
                    "sse_id": record["sse"]["ORG_BULLETIN_ID"],
                    "symbol": record["sse"]["SECURITY_CODE"],
                    "reason": str(exc),
                }
            )
    ordered = normalize(events)
    conflicts = []
    for security_id in sorted({e["security_id"] for e in ordered}):
        history = [e for e in ordered if e["security_id"] == security_id]
        for previous, current in pairwise(history):
            if previous["effective_from"] == current["effective_from"]:
                issue = previous["status"] != current["status"]
                reason = "CONFLICTING_SAME_DATE_STATUS"
            else:
                issue = previous["status"] != current["old_status"]
                reason = "MISSING_INTERVENING_TRANSITION_OR_CONFLICT"
            if issue:
                conflicts.append(
                    {
                        "security_id": security_id,
                        "reason": reason,
                        "previous_document": previous["sse_announcement_id"],
                        "next_document": current["sse_announcement_id"],
                    }
                )
    save(root / "conflicts.json", conflicts)
    save(root / "normalized-events.json", ordered)
    save(root / "unresolved-documents.json", unresolved)
    with master.open() as handle:
        securities = {r["symbol"]: r for r in csv.DictReader(handle)}
    candidate_symbols: set[str] = set()
    for path in sorted((sse_snapshot / "metadata").glob("*.json")):
        for group in json.loads(path.read_bytes())["pageHelp"]["data"]:
            candidate_symbols.update(
                r["SECURITY_CODE"] for r in group if r["SECURITY_CODE"] in securities
            )
    classifications = []
    for symbol in sorted(candidate_symbols):
        security = securities[symbol]
        classifications.append(
            {
                "security_id": security["security_id"],
                "classification": "UNRESOLVED",
                "from_inclusive": max("2023-01-01", security["listing_date"]),
                "to_inclusive": min("2024-07-31", security["delisting_date"] or "2024-07-31"),
                "reason": "Candidate selection does not prove complete transitions or baseline.",
                "parsed_events": sum(e["symbol"] == symbol for e in ordered),
                "last_known_pilot_start_status": status_on(
                    ordered, security["security_id"], "2023-01-01"
                ),
            }
        )
    save(root / "candidate-classifications.json", classifications)
    summary = {
        "normalized_event_sha256": sha(canonical(ordered)),
        "events": len(ordered),
        "event_types": dict(Counter(e["event_type"] for e in ordered)),
        "parsed_securities": len({e["security_id"] for e in ordered}),
        "unresolved_documents": len(unresolved),
        "candidate_securities": len(classifications),
        "classification_counts": dict(Counter(r["classification"] for r in classifications)),
        "conflicts_or_history_gaps": len(conflicts),
        "pilot_event_types": dict(
            Counter(
                e["event_type"]
                for e in ordered
                if "2023-01-01" <= e["effective_from"] <= "2024-07-31"
            )
        ),
        "pilot_risk_securities_lower_bound": len(
            {
                e["security_id"]
                for e in ordered
                if "2023-01-01" <= e["effective_from"] <= "2024-07-31" and e["status"] != "NORMAL"
            }
        ),
        "last_known_risk_at_pilot_start_not_coverage_certified": sum(
            r["last_known_pilot_start_status"] in {"ST", "STAR_ST"} for r in classifications
        ),
        "SSE_HISTORICAL_ST_RECONSTRUCTION": "PARTIAL" if ordered else "FAIL",
        "PILOT_A_SHARE_DATA_READINESS": "BLOCKED",
    }
    save(root / "event-summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--sse-snapshot", type=Path, required=True)
    args = parser.parse_args()
    build(args.root, args.master, args.sse_snapshot)
