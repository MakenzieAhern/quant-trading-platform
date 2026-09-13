"""Cache page-addressable extraction of retained official PDFs; never accept event terms."""

import argparse
import json
import unicodedata
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable


def main() -> None:
    from pypdf import PdfReader, __version__

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", default="batch-v3")
    args = parser.parse_args()
    manifest = json.loads((args.root / args.batch / "source-manifest.json").read_bytes())
    for row in manifest["documents"]:
        if row["retrieval_status"] != "PASS":
            continue
        pdf = args.root / row["source_path"]
        if sha256_file(pdf) != row["source_sha256"]:
            raise ValueError("PDF_CHECKSUM_CHANGED")
        output = args.root / "batch-v1/text" / (row["source_sha256"] + ".json")
        if output.exists():
            continue
        pages = [
            unicodedata.normalize("NFKC", page.extract_text()) for page in PdfReader(pdf).pages
        ]
        write_immutable(
            output,
            canonical_json_bytes(
                dict(
                    source_sha256=row["source_sha256"],
                    parser_version="PYPDF_NFKC_PAGE_EXTRACTION_V1",
                    pypdf_version=__version__,
                    pages=pages,
                    event_acceptance="NOT_PERFORMED",
                )
            )
            + b"\n",
        )
        print(json.dumps(dict(issuer=row["issuer"], pages=len(pages))), flush=True)


if __name__ == "__main__":
    main()
