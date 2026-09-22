"""Independent name-history coverage oracle; never a source of effective dates."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pypdf import PdfReader

from scripts.reconcile_sse_cninfo import (
    QUERY,
    STATIC,
    canonical,
    fetch,
    match,
    publication,
    save,
    sha,
)
from scripts.sse_st_coverage import END, START, assert_completeness, intervals_for
from scripts.sse_st_events import extract, normalize, status


def anchor_names(pages: list[str]) -> dict[str, dict[str, Any]]:
    """The year-end shareholder table, NOT current names or annual high/low rows."""
    if len(pages) < 7 or "2022年1月1日至2022年12月31日" not in re.sub(r"\s+", "", pages[6]):
        raise ValueError("WRONG_ANCHOR_PERIOD")
    result: dict[str, dict[str, Any]] = {}
    for number, page in enumerate(pages, 1):
        if "年末个股股东持股情况" not in page:
            continue
        for row in re.finditer(r"(?m)^(\d{6})[ \t]+([^\n\d]+?)\s+\d", page):
            symbol, name = row[1], re.sub(r"\s+", "", row[2])
            if symbol in result:
                raise ValueError("DUPLICATE_ANCHOR_SECURITY")
            result[symbol] = {
                "symbol": symbol,
                "name": name,
                "status": status(name),
                "page": number,
                "as_of": "2022-12-31",
            }
    if not result:
        raise ValueError("EMPTY_ANCHOR")
    return result


def name_key(name: str) -> str:
    """Sina sometimes appends the B-share name in parentheses to the A-share name."""
    return re.sub(r"\s+", "", re.split(r"[\uff08(]", name)[0]).translate(
        str.maketrans("\u2217\uff0a\ufe61", "***")
    )


def explain_names(
    names: list[str], events: list[dict[str, Any]], anchor: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Require entry/exit evidence or anchored left boundary; never name-order dates."""
    events = sorted(events, key=lambda e: (e["effective_from"], e["cninfo_document_id"]))
    result = []
    for token in names:
        state = status(token)
        if state == "NORMAL":
            continue
        key = name_key(token)
        entries = [
            e
            for e in events
            if name_key(e["new_name"]) == key and e["status"] == state and e["old_status"] != state
        ]
        exits = [
            e
            for e in events
            if name_key(e["old_name"]) == key and e["old_status"] == state and e["status"] != state
        ]
        anchored = anchor is not None and name_key(anchor["name"]) == key
        # A dated entry alone cannot prove an exit or a still-active right boundary.
        # An official anchor can censor the left boundary, never invent an exit.
        explained = any(
            any(entry["effective_from"] <= exit_["effective_from"] for entry in entries)
            or (anchored and anchor is not None and anchor["as_of"] <= exit_["effective_from"])
            for exit_ in exits
        )
        result.append(
            {
                "token": token,
                "name_key": key,
                "status": state,
                "explained": explained,
                "anchor_supported": anchored,
                "entry_documents": [e["cninfo_document_id"] for e in entries],
                "exit_documents": [e["cninfo_document_id"] for e in exits],
                "reason": "DATED_ENTRY_OR_ANCHOR_AND_DATED_EXIT"
                if explained
                else "EVENT_LEDGER_COVERAGE_GAP: entry/exit or censoring evidence incomplete",
            }
        )
    return result


def closure_audit(
    master_path: Path, candidates_path: Path, output: Path, prior: Path, snapshot: Path
) -> None:
    master = sorted(csv.DictReader(master_path.open()), key=lambda s: s["security_id"])
    candidates = {s["security_id"] for s in json.loads(candidates_path.read_bytes())}
    pdf = output / "anchor/yearbook-2023.pdf"
    pdf_sha = sha(pdf.read_bytes())
    meta = json.loads(pdf.with_suffix(".pdf.meta.json").read_bytes())
    if pdf_sha != meta["sha256"]:
        raise ValueError("ANCHOR_CHECKSUM_MISMATCH")
    anchors = anchor_names(json.loads((output / "anchor/yearbook-2023-text.json").read_bytes()))
    # Independently extracted page layout must reproduce every code/name pair.
    other: dict[str, str] = {}
    for page in json.loads((output / "anchor/yearbook-2023-fitz-text.json").read_bytes()):
        if "年末个股股东持股情况" in page:
            other.update(
                (m[1], name_key(m[2])) for m in re.finditer(r"(?m)^(\d{6})\s*\n([^\n]+)\n", page)
            )
    if {k: name_key(v["name"]) for k, v in anchors.items()} != other:
        raise ValueError("ANCHOR_EXTRACTION_DISAGREEMENT")
    eligible = [s for s in master if s["listing_date"] <= START <= (s["delisting_date"] or END)]
    if any(s["symbol"] not in anchors for s in eligible):
        raise ValueError("ANCHOR_MISSING_ELIGIBLE_SECURITY")
    manifest = json.loads((snapshot / "source-manifest.json").read_bytes())
    expected = manifest.pop("manifest_sha256")
    if sha(canonical(manifest)) != expected:
        raise ValueError("SSE_INDEX_MANIFEST_MISMATCH")
    month_pages: dict[str, list[dict[str, Any]]] = {}
    for entry in manifest["pages"]:
        raw = (snapshot / entry["relative_path"]).read_bytes()
        if sha(raw) != entry["sha256"]:
            raise ValueError("SSE_INDEX_PAGE_MISMATCH")
        month_pages.setdefault(entry["month"], []).append(entry)
    for year in (2023, 2024):
        for month in range(1, 13 if year == 2023 else 8):
            rows = month_pages[f"{year}-{month:02}"]
            if {r["page"] for r in rows} != set(range(1, rows[0]["page_count"] + 1)):
                raise ValueError("SSE_INDEX_PAGINATION_GAP")
    events = json.loads((prior / "normalized-events.json").read_bytes())
    additional = output / "additional-reconciliation.json"
    if additional.exists():
        reparsed = json.loads(additional.read_bytes())
        new_events = []
        for record in reparsed:
            if record["match_confidence"] != "EXACT":
                continue
            document = record["cninfo"][0]["announcementId"]
            if (
                sha((output / "documents" / (document + ".pdf")).read_bytes())
                != record["cninfo_document_sha256"]
            ):
                raise ValueError("ADDITIONAL_DOCUMENT_CHECKSUM_MISMATCH")
            try:
                event = extract(
                    json.loads((output / "text" / (document + ".json")).read_bytes()), record
                )
            except ValueError as exc:
                record.pop("event", None)
                record["parse_error"] = str(exc)
            else:
                record.pop("parse_error", None)
                event["retrieved_at_utc"] = json.loads(
                    (output / "documents" / (document + ".pdf.meta.json")).read_bytes()
                )["retrieved_at_utc"]
                record["event"] = event
                new_events.append(event)
        # Acquisition records remain untouched; this is a separate offline parser audit.
        save(output / "accepted-additional-events.json", normalize(new_events))
        save(output / "additional-parser-audit.json", reparsed)
        events.extend(new_events)
    events = normalize(events)
    names = sorted(
        json.loads((output / "name-audit.json").read_bytes()), key=lambda s: s["security_id"]
    )
    crosscheck = []
    for row in names:
        history = [e for e in events if e["security_id"] == row["security_id"]]
        explanations = explain_names(row.get("names", []), history, anchors.get(row["symbol"]))
        crosscheck.append(
            {
                **row,
                "tokens": explanations,
                "unexplained": sum(not t["explained"] for t in explanations),
            }
        )
    excluded = {r["security_id"] for r in crosscheck if r["unexplained"]}
    intervals, audit = [], []
    for security in master:
        identity, code = security["security_id"], security["symbol"]
        history = [
            e
            for e in events
            if e["security_id"] == identity and START <= e["effective_from"] <= END
        ]
        initial = anchors.get(code)
        if (
            initial is None
            and security["listing_date"] > "2022-12-31"
            and status(security["name"]) == "NORMAL"
        ):
            initial = {
                "symbol": code,
                "name": security["name"],
                "status": "NORMAL",
                "as_of": security["listing_date"],
                "kind": "NORMAL_NEW_LISTING",
                "source_url": security["source_url"],
                "assumption": (
                    "User-authorized initial NORMAL for ordinary new A-share listing; "
                    "not inferred from missing events."
                ),
            }
        if initial is None:
            excluded.add(identity)
            points = []
        else:
            points = [
                {
                    "known_on": max(START, initial["as_of"]),
                    "effective_from": max(START, initial["as_of"]),
                    "status": initial["status"],
                }
            ]
        state = initial["status"] if initial else "EXCLUDED"
        chain_gaps = []
        for event in sorted(history, key=lambda e: (e["effective_from"], e["sse_announcement_id"])):
            if event["old_status"] != state:
                chain_gaps.append(event["cninfo_document_id"])
                excluded.add(identity)
            state = event["status"]
            points.append(
                {
                    "known_on": max(
                        event["sse_publication_date"], event["cninfo_publication_date"]
                    ),
                    "effective_from": event["effective_from"],
                    "status": state,
                }
            )
        rows = intervals_for(security, points)
        # These are evidence-replay admissions, NOT dataset acceptance. The global
        # coverage gate stays PARTIAL while any oracle lifecycle remains unexplained.
        for row in rows:
            row["coverage_certified"] = identity not in excluded
            row["status"] = row["evidence_status"] if identity not in excluded else "EXCLUDED"
        intervals.extend(rows)
        classification = (
            "CONSERVATIVELY_EXCLUDED"
            if identity in excluded
            else (
                "RESOLVED_TRANSITION_TIMELINE"
                if any(e["event_type"] != "STATUS_CONFIRMATION" for e in history)
                else "RESOLVED_ST_AT_PILOT_START"
                if initial and initial["status"] == "ST"
                else "RESOLVED_STAR_ST_AT_PILOT_START"
                if initial and initial["status"] == "STAR_ST"
                else "RESOLVED_NORMAL"
            )
        )
        audit.append(
            {
                "security_id": identity,
                "symbol": code,
                "is_candidate": identity in candidates,
                "classification": classification,
                "anchor": initial,
                "events": history,
                "chain_gaps": chain_gaps,
                "dataset_admission_authorized": False,
                "reason": "EVENT_CHAIN_CONFLICT"
                if chain_gaps
                else "UNEXPLAINED_NAME_HISTORY"
                if identity in excluded and initial
                else "DATED_IPO_NAME_NOT_YET_VERIFIED"
                if initial is None
                else "ANCHOR_AND_INDEX_REPLAY",
            }
        )
    sessions = json.loads((prior / "calendar/pilot-sessions.json").read_bytes())
    metrics = assert_completeness(master, intervals, sessions)
    initial_counts = Counter(anchors[s["symbol"]]["status"] for s in eligible)
    summary = {
        "scope": "PROVISIONAL_EVIDENCE_REPLAY_NOT_DATASET_ADMISSION",
        "official_anchor_found": True,
        "anchor_date": "2022-12-31",
        "anchor_last_trading_session": "2022-12-30",
        "anchor_source": meta["url"],
        "anchor_sha256": pdf_sha,
        "anchor_parser_version": "sse-yearbook-2023-yearend-shareholders-v1",
        "sse_index_manifest_sha256": expected,
        "security_master_sha256": sha(master_path.read_bytes()),
        "anchor_temporality": (
            "Official retrospective 2022 year-end state, not a claim of pre-2023 publication."
        ),
        "anchor_rows": len(anchors),
        "anchor_eligible": len(eligible),
        "pilot_start_states_from_anchor": dict(initial_counts),
        "pilot_start_states_after_local_exclusions": dict(
            Counter(
                "EXCLUDED" if s["security_id"] in excluded else anchors[s["symbol"]]["status"]
                for s in eligible
            )
        ),
        "pilot_start_unknown": 0,
        "earliest_event_date": min(e["effective_from"] for e in events),
        "latest_event_date": max(e["effective_from"] for e in events),
        "official_event_records": len(events),
        "pilot_event_records": sum(START <= e["effective_from"] <= END for e in events),
        "combined_event_sha256": sha(canonical(events)),
        "securities_checked": len(names),
        "control_non_candidates": sum(r["is_control"] for r in names),
        "name_classifications": dict(Counter(r["classification"] for r in names)),
        "historical_st_names_found": sum(
            t["status"] == "ST" for r in crosscheck for t in r["tokens"]
        ),
        "historical_star_st_names_found": sum(
            t["status"] == "STAR_ST" for r in crosscheck for t in r["tokens"]
        ),
        "explained_by_official_events_or_anchor": sum(
            t["explained"] for r in crosscheck for t in r["tokens"]
        ),
        "unexplained_name_histories": sum(bool(r["unexplained"]) for r in crosscheck),
        "unexplained_control_histories": sum(
            bool(r["unexplained"]) and r["is_control"] for r in crosscheck
        ),
        "unexplained_histories_in_provisional_admissions": sum(
            bool(r["unexplained"]) for r in crosscheck if r["security_id"] not in excluded
        ),
        "candidate_classifications": dict(
            Counter(r["classification"] for r in audit if r["is_candidate"])
        ),
        "master_securities": len(master),
        "provisional_replay_admissions": len(master) - len(excluded),
        "dataset_admissions": 0,
        "new_ipo_missing_dated_name": sum(r["anchor"] is None for r in audit),
        "EVENT_LEDGER_COVERAGE": "PARTIAL",
        "HISTORICAL_NAME_CROSSCHECK": "PARTIAL",
        "SSE_HISTORICAL_ST_RECONSTRUCTION": "PARTIAL",
        "PILOT_A_SHARE_DATA_READINESS": "BLOCKED",
        "PILOT_START_STATUS": "PASS_FROM_OFFICIAL_ANCHOR",
        "dataset_created": False,
        "excluded_universe_percentage": 100 * len(excluded) / len(master),
        **metrics,
    }
    # Do not let a diagnostic, locally resolved replay bypass the global coverage gate.
    for row in intervals:
        row["evidence_replay_resolved"] = row["coverage_certified"]
        row["coverage_certified"] = False
    for name, value in {
        "combined-normalized-events": events,
        "pilot-start-anchor": anchors,
        "name-crosscheck": crosscheck,
        "security-closure-audit": audit,
        "closure-intervals": intervals,
        "closure-summary": summary,
    }.items():
        save(output / (name + ".json"), value)
    files = [
        {"path": p.relative_to(output).as_posix(), "sha256": sha(p.read_bytes())}
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "closure-manifest.json" and not p.name.endswith(".tmp")
    ]
    evidence_manifest = {"files": files, "parser_version": "sse-st-closure-v1"}
    save(
        output / "closure-manifest.json",
        {
            **evidence_manifest,
            "manifest_sha256": sha(canonical(evidence_manifest)),
        },
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in {"daily", "excluded_security_days_by_id"}
            },
            indent=2,
        )
    )


def historical_names(raw: bytes, symbol: str) -> list[str]:
    text = raw.decode("gb18030")
    if not re.search(r'page_symbol\s*=\s*"sh' + re.escape(symbol) + '"', text):
        raise ValueError("NAME_HISTORY_IDENTITY_MISMATCH")
    match = re.search(r"证券简称更名历史[\uff1a:]?</td>\s*<td[^>]*>(.*?)</td>", text, re.S)
    if not match:
        raise ValueError("NAME_HISTORY_UNAVAILABLE")
    names = html.unescape(re.sub(r"<[^>]+>", " ", match[1])).split()
    if not names:
        raise ValueError("NAME_HISTORY_UNAVAILABLE")
    return names


def controls(master: list[dict[str, str]], candidates: set[str]) -> list[dict[str, str]]:
    available = [s for s in master if s["security_id"] not in candidates]
    chosen = {s["security_id"]: s for s in available if s["delisting_date"]}
    for board, cutoff in (("SSE_MAIN", "2020-01-01"), ("STAR", "2021-01-01")):
        for recent in (False, True):
            group = [
                s
                for s in available
                if (s["board"] == "SSE_MAIN") == (board == "SSE_MAIN")
                and (s["listing_date"] >= cutoff) == recent
            ]
            group.sort(key=lambda s: sha(("sse-closure-control-v1:" + s["security_id"]).encode()))
            chosen.update((s["security_id"], s) for s in group[:25])
    if len(chosen) < 100:
        raise ValueError("INSUFFICIENT_STRATIFIED_CONTROLS")
    return [chosen[k] for k in sorted(chosen)]


def acquire_names(master_path: Path, candidates_path: Path, output: Path) -> None:
    master = list(csv.DictReader(master_path.open()))
    candidates = {s["security_id"] for s in json.loads(candidates_path.read_bytes())}
    sample = controls(master, candidates)
    selected = sorted(
        [s for s in master if s["security_id"] in candidates] + sample,
        key=lambda s: s["security_id"],
    )
    save(output / "control-sample.json", sample)

    def get(security: dict[str, str]) -> dict[str, Any]:
        code = security["symbol"]
        result: dict[str, Any] = {
            "security_id": security["security_id"],
            "symbol": code,
            "is_control": security["security_id"] not in candidates,
            "parser_version": "sina-name-oracle-v1",
            "supplies_dates": False,
        }
        try:
            raw = fetch(
                output,
                f"names/{code}.html",
                f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpInfo/stockid/{code}.phtml",
            )
            names = historical_names(raw, code)
            states = {status(n) for n in names}
            result.update(
                names=names,
                sha256=sha(raw),
                classification="HAS_STAR_ST_HISTORY"
                if "STAR_ST" in states
                else "HAS_ST_HISTORY"
                if "ST" in states
                else "NO_ST_NAME_HISTORY",
            )
        except (OSError, UnicodeError, ValueError) as exc:
            result.update(classification="NAME_HISTORY_UNAVAILABLE", reason=str(exc))
        return result

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(get, selected):
            results.append(result)
            save(output / "name-audit.json", results)
            print(f"name histories={len(results)}/{len(selected)}", flush=True)


def lookup_gaps(output: Path, source: Path) -> None:
    """Target only oracle-flagged issuers; metadata is not accepted event evidence."""
    gaps = [
        r for r in json.loads((output / "name-crosscheck.json").read_bytes()) if r["unexplained"]
    ]
    anchors = json.loads((output / "pilot-start-anchor.json").read_bytes())
    orgs = {
        r["cninfo"][0]["secCode"]: r["cninfo"][0]["orgId"]
        for r in json.loads((source / "reconciliation.json").read_bytes())
    }
    for path in (output / "oracle-lookups").glob("*.json"):
        if path.name.endswith(".meta.json"):
            continue
        for row in json.loads(path.read_bytes()).get("announcements") or []:
            orgs[row["secCode"]] = row["orgId"]

    def get(row: dict[str, Any]) -> dict[str, Any]:
        code = row["symbol"]
        org = orgs.get(code)
        base: dict[str, object] = {
            "pageNum": 1,
            "pageSize": 30,
            "column": "sse",
            "tabName": "fulltext",
            "secid": "",
            "plate": "",
            "category": "",
            "trade": "",
            "seDate": "1990-01-01~2026-09-10",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "false",
        }
        if org is None:
            params = {**base, "stock": "", "searchkey": anchors[code]["name"]}
            data = json.loads(fetch(output, f"oracle-lookups/{code}-identity.json", QUERY, params))
            found = {r["orgId"] for r in data.get("announcements") or [] if r["secCode"] == code}
            if len(found) != 1:
                return {
                    "security_id": row["security_id"],
                    "complete": False,
                    "reason": "ORG_ID_UNRESOLVED",
                }
            org = next(iter(found))
        records: list[dict[str, Any]] = []
        for page in range(1, 21):
            params = {**base, "stock": f"{code},{org}", "searchkey": "风险警示", "pageNum": page}
            data = json.loads(
                fetch(output, f"oracle-lookups/{code}-risk-p{page:03}.json", QUERY, params)
            )
            values = data.get("announcements") or []
            if any(r["secCode"] != code for r in values):
                raise ValueError("QUERY_DID_NOT_FILTER_SECURITY_STOP")
            records.extend(values)
            if not data["hasMore"]:
                break
        return {
            "security_id": row["security_id"],
            "complete": not data["hasMore"],
            "records": records,
            "purpose": "ORACLE_GAP_INVESTIGATION_ONLY_NOT_PILOT_EVENTS",
        }

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for value in pool.map(get, gaps):
            results.append(value)
            save(output / "targeted-history-metadata.json", results)
            print(f"targeted histories={len(results)}/{len(gaps)}", flush=True)


def reconcile_gaps(output: Path, source: Path) -> None:
    """Acquire only candidate state-changing disclosures uncovered by the name oracle."""
    old = {
        r["cninfo"][0]["announcementId"]
        for r in json.loads((source / "reconciliation.json").read_bytes())
    }
    selected = {}
    for history in json.loads((output / "targeted-history-metadata.json").read_bytes()):
        for row in history.get("records", []):
            title = row["announcementTitle"]
            if (
                re.search("实施|实行|撤销|取消", title)
                and not re.search(
                    "申请|可能|进展|预计|预审计|风险提示|会计师|律师|核查|保荐|审计|回复|监管工作函|存在被|补充|更正",
                    title,
                )
                and row["announcementId"] not in old
            ):
                selected[row["announcementId"]] = row
    dates = sorted({publication(r) for r in selected.values()})

    def get_day(day: str) -> list[dict[str, Any]]:
        cn_rows = [r for r in selected.values() if publication(r) == day]
        sse_rows = []
        hashes = {}
        for page in range(1, 41):
            params = {
                "isPagination": "true",
                "pageHelp.pageSize": 25,
                "pageHelp.cacheSize": 1,
                "pageHelp.pageNo": page,
                "START_DATE": day,
                "END_DATE": day,
                "SECURITY_CODE": "",
                "TITLE": "",
                "BULLETIN_TYPE": "31",
                "stockType": "",
            }
            url = "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?" + urlencode(
                params
            )
            raw = fetch(
                output,
                f"ledger-days/{day}-p{page:03}.json",
                url,
                referer="https://www.sse.com.cn/disclosure/listedinfo/announcement/",
            )
            payload = json.loads(raw)
            help_ = payload["pageHelp"]
            for group in help_["data"]:
                for row in group:
                    sse_rows.append(row)
                    hashes[row["ORG_BULLETIN_ID"]] = sha(raw)
            if page >= help_["pageCount"]:
                break
        else:
            raise ValueError("SSE_DAILY_PAGINATION_INCOMPLETE")
        results = []
        for cn in cn_rows:
            matches = [r for r in sse_rows if match(r, [cn], issuer_prefix=True)[0] == "EXACT"]
            category = "31"
            if not matches:
                # Older genuine warning announcements were catalogued as Other.
                # A single issuer/day fallback audits that gap without downloading
                # unrelated announcements or assuming empty category == no event.
                params = {
                    **params,
                    "pageHelp.pageNo": 1,
                    "SECURITY_CODE": cn["secCode"],
                    "BULLETIN_TYPE": "",
                }
                for fallback_page in range(1, 41):
                    params["pageHelp.pageNo"] = fallback_page
                    suffix = "all" if fallback_page == 1 else f"all-p{fallback_page:03}"
                    raw = fetch(
                        output,
                        f"ledger-fallback/{cn['secCode']}-{day}-{suffix}.json",
                        "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?"
                        + urlencode(params),
                        referer="https://www.sse.com.cn/disclosure/listedinfo/announcement/",
                    )
                    payload = json.loads(raw)["pageHelp"]
                    for group in payload["data"]:
                        for row in group:
                            if match(row, [cn], issuer_prefix=True)[0] == "EXACT":
                                matches.append(row)
                                hashes[row["ORG_BULLETIN_ID"]] = sha(raw)
                    if fallback_page >= payload["pageCount"]:
                        break
                else:
                    raise ValueError("SSE_ISSUER_DAY_PAGINATION_INCOMPLETE")
                category = "TARGETED_ALL_CATEGORIES"
            # Overlapping public pages can repeat an identical metadata row.
            # Distinct rows, even for one document id, remain ambiguous.
            matches = list({canonical(row): row for row in matches}.values())
            result: dict[str, Any] = {
                "cninfo": [cn],
                "match_confidence": "NO_MATCH",
                "scope": "ORACLE_LIFECYCLE_AUDIT",
            }
            if len(matches) == 1:
                sse = matches[0]
                result.update(
                    sse=sse,
                    match_confidence="EXACT",
                    index_category=category,
                    match_method="security+date+exact_subject+issuer_prefix",
                    sse_metadata_snapshot_sha256=hashes[sse["ORG_BULLETIN_ID"]],
                )
                path = cn["adjunctUrl"]
                if not re.fullmatch(r"finalpage/\d{4}-\d{2}-\d{2}/\d+\.pdf", path, re.I):
                    raise ValueError("UNEXPECTED_CNINFO_DOCUMENT_PATH")
                raw = fetch(output, f"documents/{cn['announcementId']}.pdf", STATIC + path)
                if not raw.startswith(b"%PDF"):
                    raise ValueError("NON_PDF_RESPONSE")
                result["cninfo_document_sha256"] = sha(raw)
                pages = [p.extract_text() for p in PdfReader(io.BytesIO(raw)).pages]
                save(output / "text" / (cn["announcementId"] + ".json"), pages)
                try:
                    result["event"] = extract(pages, result)
                except ValueError as exc:
                    result["parse_error"] = str(exc)
            elif matches:
                result["match_confidence"] = "AMBIGUOUS"
            results.append(result)
        return results

    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index, rows in enumerate(pool.map(get_day, dates), 1):
            results.extend(rows)
            save(output / "additional-reconciliation.json", results)
            print(
                f"reconciled dates={index}/{len(dates)} records={len(results)}/{len(selected)}",
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--lookups", type=Path, help="Preserved CNINFO source directory")
    parser.add_argument("--reconcile", type=Path, help="Preserved CNINFO source directory")
    args = parser.parse_args()
    if args.reconcile:
        reconcile_gaps(args.output, args.reconcile)
    elif args.lookups:
        lookup_gaps(args.output, args.lookups)
    elif args.audit:
        if not args.prior or not args.snapshot:
            parser.error("--audit requires --prior and --snapshot")
        closure_audit(args.master, args.candidates, args.output, args.prior, args.snapshot)
    else:
        acquire_names(args.master, args.candidates, args.output)
