"""Cache page-addressable extraction of retained official PDFs; never accept event terms."""

import argparse
import json
import unicodedata
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable


def cached_extractions(roots: list[Path]) -> dict[str, bytes]:
    result = {}
    for root in roots:
        for path in root.rglob("batch-v1/text/*.json"):
            raw = path.read_bytes()
            value = json.loads(raw)
            source_sha256 = value.get("source_sha256")
            if source_sha256 != path.stem:
                raise ValueError("EXTRACTION_CACHE_IDENTITY_MISMATCH")
            if source_sha256 in result and result[source_sha256] != raw:
                raise ValueError("CONFLICTING_EXTRACTION_CACHES")
            result[source_sha256] = raw
    return result


def documents(root: Path, batch: str, from_receipts: bool) -> list[dict]:
    if from_receipts:
        return [
            json.loads(path.read_bytes())
            for path in sorted((root / batch / "receipts").glob("*.json"))
        ]
    return json.loads((root / batch / "source-manifest.json").read_bytes())["documents"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", default="batch-v3")
    parser.add_argument("--engine", choices=("pypdf", "pymupdf"), default="pypdf")
    parser.add_argument("--document-sha256", action="append")
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--from-receipts", action="store_true")
    args = parser.parse_args()
    rows = documents(args.root, args.batch, args.from_receipts)
    selected = set(args.document_sha256 or ())
    available = {row.get("source_sha256") for row in rows}
    if selected - available:
        raise ValueError("SELECTED_DOCUMENT_NOT_IN_SOURCE_MANIFEST")
    cached = cached_extractions(args.source_root) if args.engine == "pypdf" else {}
    for row in rows:
        if row["retrieval_status"] != "PASS" or (selected and row["source_sha256"] not in selected):
            continue
        pdf = args.root / row["source_path"]
        if sha256_file(pdf) != row["source_sha256"]:
            raise ValueError("PDF_CHECKSUM_CHANGED")
        output = (
            args.root
            / ("batch-v1/text-pymupdf" if args.engine == "pymupdf" else "batch-v1/text")
            / (row["source_sha256"] + ".json")
        )
        if output.exists():
            continue
        if row["source_sha256"] in cached:
            write_immutable(output, cached[row["source_sha256"]])
            print(json.dumps(dict(issuer=row["issuer"], extraction="REUSED")), flush=True)
            continue
        if args.engine == "pymupdf":
            import pymupdf

            with pymupdf.open(pdf) as document:
                pages = [unicodedata.normalize("NFKC", page.get_text()) for page in document]
            parser_version = f"PYMUPDF_NFKC_PAGE_EXTRACTION_V1:{pymupdf.__version__}"
        else:
            from pypdf import PdfReader, __version__

            pages = [
                unicodedata.normalize("NFKC", page.extract_text()) for page in PdfReader(pdf).pages
            ]
            parser_version = f"PYPDF_NFKC_PAGE_EXTRACTION_V1:{__version__}"
        write_immutable(
            output,
            canonical_json_bytes(
                dict(
                    source_sha256=row["source_sha256"],
                    parser_version=parser_version,
                    pages=pages,
                    event_acceptance="NOT_PERFORMED",
                )
            )
            + b"\n",
        )
        print(json.dumps(dict(issuer=row["issuer"], pages=len(pages))), flush=True)


if __name__ == "__main__":
    main()
