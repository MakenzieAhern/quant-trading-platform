"""Offline source reconciliation for new Pilot members; never publish a dataset."""

import argparse
import json
import re
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from app.domain.markets.security import InstrumentClassification
from scripts.classify_pilot_instruments import ipo_type
from scripts.reconcile_sse_cninfo import canonical, match, save, sha
from scripts.sse_st_closure import anchor_names
from scripts.sse_st_events import compact, extract


def delisting_start(text, symbol):
    text = compact(text)
    if not re.search(r"证券代码[\uff1a:]" + re.escape(symbol), text):
        raise ValueError("WRONG_DELISTING_ISSUER")
    matches = re.findall(r"进入退市整理期的起始日为(20\d{2})年(\d{1,2})月(\d{1,2})日", text)
    dates = {date(*map(int, row)).isoformat() for row in matches}
    if len(dates) != 1:
        raise ValueError("DELISTING_START_UNRESOLVED")
    return dates.pop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    staging = args.staging
    master_root = staging / "pilot-v2-master"
    root = staging / "pilot-v2-notices"
    impact = json.loads((master_root / "master-impact.json").read_bytes())
    if (
        impact["conflicts"]
        or impact["removed"]
        or any(
            d["missing"] or d["extra"] for d in impact["independent_baseline_differences"].values()
        )
    ):
        raise ValueError("MASTER_RECONCILIATION_INCOMPLETE")
    anchors = anchor_names(
        json.loads(
            (staging / "sse-st-pilot/closure-20260910/anchor/yearbook-2023-text.json").read_bytes()
        )
    )
    reconciled = json.loads((root / "targeted-reconciliation.json").read_bytes())
    report = []
    for sid in impact["new_active_during_pilot"]:
        symbol = sid.rsplit(":", 1)[1]
        inventory = json.loads((root / f"{symbol}-inventory.json").read_bytes())
        member = inventory["member"]
        provenance = {}
        for source in inventory["sources"]:
            raw = (root / source["path"]).read_bytes()
            if sha(raw) != source["sha256"]:
                raise ValueError("DISCLOSURE_SNAPSHOT_CHANGED")
            for group in json.loads(raw)["result"]:
                for row in group:
                    provenance[row["URL"]] = source
        events, documents = [], []
        for original in reconciled:
            if (
                original["sse"]["SECURITY_CODE"] != symbol
                or original["match_confidence"] != "EXACT"
            ):
                continue
            record = {
                **original,
                "match_method": "security+publication_date+punctuation_normalized_full_title",
                "sse_metadata_snapshot_sha256": provenance[original["sse"]["URL"]]["sha256"],
            }
            if match(record["sse"], record["cninfo"])[0] != "EXACT":
                raise ValueError("RECONCILIATION_NOT_REPRODUCED")
            path = root / "documents" / (record["cninfo"][0]["announcementId"] + ".pdf")
            if sha(path.read_bytes()) != record["cninfo_document_sha256"]:
                raise ValueError("DOCUMENT_CHANGED")
            pages = [p.extract_text() for p in PdfReader(path).pages]
            documents.append(dict(record=record, path=str(path.relative_to(staging)), pages=pages))
            if "进入退市整理期交易的公告" in record["sse"]["TITLE"]:
                effective = delisting_start("\n".join(pages), symbol)
                if effective < record["sse"]["SSEDATE"]:
                    raise ValueError("RETROSPECTIVE_DELISTING")
                events.append(
                    dict(
                        status="DELISTING_PERIOD",
                        effective_from=effective,
                        source=record,
                        old_status=anchors[symbol]["status"],
                    )
                )
            elif "风险警示" in record["sse"]["TITLE"] and "继续" not in record["sse"]["TITLE"]:
                events.append(extract(pages, record))
        ipo = [
            r
            for r in inventory["notices"]
            if ipo_type(r, symbol, member["listing_date"]) is not None
        ]
        if ipo:
            types = {ipo_type(r, symbol, member["listing_date"]).value for r in ipo}
            if types != {"COMMON_A_SHARE"}:
                raise ValueError("NEW_INSTRUMENT_NOT_CONFIRMED_ORDINARY")
            row = min(ipo, key=lambda r: (r["SSEDATE"], r["URL"]))
            source = provenance[row["URL"]]
            path = root / source["path"]
            url, digest = source["url"], source["sha256"]
            evidence = dict(ipo_notice_metadata=row)
        else:
            transfers = [d for d in documents if "转板上市公告书" in d["record"]["sse"]["TITLE"]]
            if len(transfers) != 1:
                raise ValueError("DATED_INSTRUMENT_TYPE_UNRESOLVED")
            document = transfers[0]
            text = compact("\n".join(document["pages"]))
            if "本公司A股股票" not in text or symbol not in text or "无新股发行" not in text:
                raise ValueError("TRANSFER_SHARE_CLASS_UNRESOLVED")
            row = document["record"]["sse"]
            if row["SSEDATE"] > member["listing_date"]:
                raise ValueError("FUTURE_TRANSFER_CLASSIFICATION")
            path = staging / document["path"]
            url = "https://static.cninfo.com.cn/" + document["record"]["cninfo"][0]["adjunctUrl"]
            digest = sha(path.read_bytes())
            evidence = dict(transfer_notice=document["record"], no_new_issuance=True)
        meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
        fact = InstrumentClassification(
            security_id={"value": sid},
            instrument_type="COMMON_A_SHARE",
            effective_from=member["listing_date"],
            source_url=url,
            source_publication_date=row["SSEDATE"],
            source_document_sha256=digest,
            retrieval_timestamp=meta["retrieved_at_utc"],
        )
        report.append(
            dict(
                member=member,
                anchor=anchors[symbol],
                events=events,
                classification=fact.model_dump(mode="json"),
                classification_evidence=evidence,
                inventory_sha256=sha(canonical(inventory)),
            )
        )
    save(master_root / "new-member-evidence.json", report)
    print(
        json.dumps(
            [
                dict(
                    security_id=r["member"]["security_id"],
                    anchor=r["anchor"],
                    events=[
                        dict(status=e["status"], effective_from=e["effective_from"])
                        for e in r["events"]
                    ],
                    instrument_type=r["classification"]["instrument_type"],
                )
                for r in report
            ]
        )
    )


if __name__ == "__main__":
    main()
