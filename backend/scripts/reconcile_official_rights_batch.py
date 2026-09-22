"""Reconcile retained standard direct-subscription notices; no full-census promotion."""

import argparse
import json
import re
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets import CorporateAction


def compact(pages):
    # Remove only standalone page numbers, not numbers embedded in economic terms.
    return "".join(re.sub(r"\s+", "", re.sub(r"(?m)^\s*\d{1,3}\s*$", "", p)) for p in pages)


def effective_date(text, published_on):
    match = re.search(
        r"本公告(?:刊登|见报|披露|发布|公告)当日[^;。]{0,100}?成功的(?:配股)?除权(?:基准)?日",
        text,
    )
    if not match:
        return None
    explicit = re.findall(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", match.group())
    dates = {date(*map(int, values)).isoformat() for values in explicit}
    if len(dates) > 1:
        raise ValueError("CONTRADICTORY_OFFICIAL_EX_DATES")
    return (next(iter(dates)) if dates else published_on, match.group())


def record_evidence(text, record):
    if not record:
        return None
    y, m, d = map(int, record.split("-"))
    token = f"{y}年{m}月{d}日"
    for match in re.finditer(token, text):
        nearby = text[max(0, match.start() - 20) : match.end() + 20]
        if "股权登记日" in nearby:
            return nearby
    match = re.search(r"向截至" + re.escape(token) + r"[^。]{0,100}登记在册", text)
    return match.group() if match else None


def standard_structure(text):
    ratio = re.search(r"每10股配(?:售)?[\d.]+股", text)
    payment = re.search(r"认购缴款[^。]{0,100}结束", text)
    return [ratio.group(), payment.group()] if ratio and payment else None


def reconcile(rows, documents):
    output = []
    for original in sorted(rows, key=lambda row: row["event_id"]):
        event = original["event"]
        code = event["security_id"]["value"].rsplit(":", 1)[-1]
        candidates = []
        for source, text in documents:
            if source["issuer"] != code or "H股" in source["title"] or code not in text[:600]:
                continue
            if "发行结果" not in source["title"] or "更正" in source["title"]:
                continue
            effective = effective_date(text, source["published_on"])
            record = record_evidence(text, event["record_date"])
            structure = standard_structure(text)
            if effective and effective[0] == event["ex_date"] and record and structure:
                candidates.append(
                    (source, dict(ex_date=effective[1], record=record, structure=structure))
                )
        if not candidates:
            output.append({**original, "batch_reconciliation": "OFFICIAL_TERMS_NOT_MATCHED"})
            continue
        candidates.sort(key=lambda pair: (pair[0]["published_on"], pair[0]["url"]))
        source, evidence = candidates[0]
        # Keep previously accepted event bytes; source reconciliation only adds evidence.
        if not original["issues"]:
            output.append(
                {
                    **original,
                    "batch_reconciliation": "PASS_EXISTING_ACCEPTED_EVENT_PRESERVED",
                    "batch_evidence": candidates,
                }
            )
            continue
        # Do not erase explicit contrary variant evidence when matching a standard template.
        if (
            "EXPLICIT_UNSUPPORTED_VARIANT" in original["issues"]
            or "UNSUPPORTED_CASH_COMPONENT" in original["issues"]
            or event.get("rights_variant") not in (None, "ORDINARY_NON_TRADABLE")
            or event.get("rights_event_class")
            not in (None, "STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE")
        ):
            output.append(
                {**original, "batch_reconciliation": "EXPLICIT_VARIANT_REQUIRES_RECONCILIATION"}
            )
            continue
        issuance = sorted(
            (
                s
                for s, t in documents
                if s["issuer"] == code
                and re.search(r"发行(?:的)?公告", s["title"])
                and "H股" not in s["title"]
                and s["published_on"] <= event["record_date"]
                and record_evidence(t, event["record_date"])
            ),
            key=lambda s: (s["published_on"], s["url"]),
        )
        if not issuance:
            output.append({**original, "batch_reconciliation": "PRE_EVENT_ISSUANCE_NOT_MATCHED"})
            continue
        action = CorporateAction.model_validate(
            dict(
                security_id=event["security_id"],
                action_type="RIGHTS_RELATED_EVENT",
                announcement_date=issuance[0]["published_on"],
                record_date=event["record_date"],
                effective_date=event["ex_date"],
                ex_date=event["ex_date"],
                rights_event_class="STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE",
                source_provider="CNINFO-official-issuer",
                source_version="STANDARD_RIGHTS_BATCH_V1",
                source_record_hash=canonical_sha256(dict(source=source, evidence=evidence)),
                source_document=source["title"],
                source_url=source["url"],
                source_document_sha256=source["source_sha256"],
                retrieved_at=source["retrieved_at_utc"],
                completeness="PARTIAL",
            )
        )
        if action.rights_issues():
            raise ValueError("RECONCILED_RIGHTS_MATERIAL_ISSUES")
        output.append(
            dict(
                event_id=original["event_id"],
                event=action.model_dump(mode="json"),
                event_checksum=action.event_checksum,
                classification=action.rights_classification,
                issues=action.rights_issues(),
                metadata_gaps=action.rights_metadata_gaps(),
                prior_oracle_row=original,
                batch_reconciliation="PASS_STANDARD_NO_SUBSCRIPTION",
                batch_evidence=candidates,
                pre_event_sources=issuance,
                optional_unverified_vendor_terms="PRESERVED_IN_PRIOR_ROW_NOT_PROMOTED",
                point_in_time_admission="NOT_ADMITTED_FULL_AUTHORITY_PENDING",
            )
        )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", default="batch-v3")
    args = parser.parse_args()
    batch_path = args.root / args.batch / "source-manifest.json"
    batch = json.loads(batch_path.read_bytes())
    documents = []
    for source in batch["documents"]:
        if source["retrieval_status"] != "PASS":
            continue
        if sha256_file(args.root / source["source_path"]) != source["source_sha256"]:
            raise ValueError("OFFICIAL_PDF_CHECKSUM_CHANGED")
        cache = json.loads(
            (args.root / "batch-v1/text" / (source["source_sha256"] + ".json")).read_bytes()
        )
        if (
            cache["source_sha256"] != source["source_sha256"]
            or cache["parser_version"] != "PYPDF_NFKC_PAGE_EXTRACTION_V1"
        ):
            raise ValueError("PDF_EXTRACTION_IDENTITY_MISMATCH")
        documents.append((source, compact(cache["pages"])))
    prior = json.loads(args.inventory.read_bytes())
    rows = reconcile(prior["rows"], documents)
    if rows != reconcile(list(reversed(prior["rows"])), list(reversed(documents))):
        raise ValueError("INPUT_ORDER_CHANGED_RIGHTS_REPLAY")
    result = dict(
        parser_version="STANDARD_RIGHTS_BATCH_V1",
        parser_sha256=sha256_file(Path(__file__)),
        prior_inventory_sha256=sha256_file(args.inventory),
        source_batch_sha256=sha256_file(batch_path),
        rights_events_total=len(rows),
        supported_events=sum(not r["issues"] for r in rows),
        unresolved_events=sum(bool(r["issues"]) for r in rows),
        input_order_reproducibility="PASS",
        census_status="PARTIAL_NOT_FULL_EXCHANGE_CENSUS",
        full_authority="NOT_ACCEPTED",
        rows=rows,
    )
    result["manifest_sha256"] = canonical_sha256(result)
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print(json.dumps([(r["event_id"], r["batch_reconciliation"]) for r in rows if r["issues"]]))


if __name__ == "__main__":
    main()
