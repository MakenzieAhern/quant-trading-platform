"""Alternate coordinate-deduplicated extraction for unresolved PDF identity headers only."""

import argparse
import json
import unicodedata
from pathlib import Path, PurePosixPath

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable


def main():
    import pdfplumber

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.staging / "full-sse-st-v1"
    prior = json.loads((root / "transition-parser-full-v1.json").read_bytes())
    reasons = {
        "WRONG_SECURITY_CODE",
        "PDF_SUBJECT_METADATA_MISMATCH",
        "CNINFO_NAME_NOT_PDF_HEADER",
        "WRONG_ISSUER_NAME",
    }
    selected = {r["announcement_id"] for r in prior["results"] if r.get("reason") in reasons}
    source = json.loads((root / "transition-pdfs-v1/source-manifest.json").read_bytes())
    for row in source["documents"]:
        if row["announcement_id"] not in selected:
            continue
        path = PurePosixPath(row["source_path"])
        if path.is_absolute():
            path = path.relative_to("/home/yuchen/data/research/staging")
        else:
            path = PurePosixPath("full-sse-st-v1") / path
        pdf = args.staging.joinpath(*path.parts)
        if sha256_file(pdf) != row["source_sha256"]:
            raise ValueError("PDF_SOURCE_CHANGED")
        output = args.output / (row["source_sha256"] + ".json")
        if output.exists():
            cached = json.loads(output.read_bytes())
            if cached["source_sha256"] != row["source_sha256"]:
                raise ValueError("ALTERNATE_EXTRACTION_IDENTITY_CHANGED")
            continue
        with pdfplumber.open(pdf) as document:
            pages, counts = [], []
            for page in document.pages:
                deduped = page.dedupe_chars(tolerance=1, extra_attrs=("fontname", "size"))
                pages.append(unicodedata.normalize("NFKC", deduped.extract_text() or ""))
                counts.append(dict(original=len(page.chars), deduplicated=len(deduped.chars)))
        result = dict(
            source_sha256=row["source_sha256"],
            parser_version="PDFPLUMBER_COORDINATE_DEDUPLICATION_V1",
            pdfplumber_version=pdfplumber.__version__,
            tolerance_points=1,
            same_glyph_attributes=["text", "fontname", "size"],
            pages=pages,
            character_counts=counts,
            accepted_events=0,
        )
        write_immutable(output, canonical_json_bytes(result) + b"\n")
        print(
            row["announcement_id"],
            sum(c["original"] - c["deduplicated"] for c in counts),
            flush=True,
        )


if __name__ == "__main__":
    main()
