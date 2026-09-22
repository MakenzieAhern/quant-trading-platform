"""Cache retained yearbook rights sections for independent event-census review."""

import argparse
import re
import unicodedata
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable


def main():
    from pypdf import PdfReader, __version__

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    root = args.staging / "full-master-sse-baseline-v1"
    paths = sorted((root / "raw").glob("sse-yearbook-*.pdf"))
    paths += [
        args.staging / "full-corporate-action-preflight-v1/official/sse-2011-factbook-rights.pdf",
        args.staging / "sse-st-pilot/closure-20260910/anchor/yearbook-2023.pdf",
    ]
    for path in paths:
        checksum = sha256_file(path)
        target = root / "rights-text" / f"{checksum}.json"
        if target.exists():
            print(path.name, "CACHED", flush=True)
            continue
        reader = PdfReader(path)
        matches = []
        for index in range(20, len(reader.pages)):
            text = unicodedata.normalize("NFKC", reader.pages[index].extract_text())
            compact = re.sub(r"\s+", "", text)
            if re.search(
                r"Allotmentin20\d{2}|上市公司(?:的)?配股|20\d{2}年上市公司配股概况", compact
            ):
                matches.append(dict(pdf_page=index + 1, text=text))
        write_immutable(
            target,
            canonical_json_bytes(
                dict(
                    source_path=str(path),
                    source_sha256=checksum,
                    parser_version="SSE_YEARBOOK_RIGHTS_SECTION_V1",
                    pypdf_version=__version__,
                    pages=matches,
                    event_acceptance="NOT_PERFORMED",
                )
            )
            + b"\n",
        )
        print(path.name, [p["pdf_page"] for p in matches], flush=True)


if __name__ == "__main__":
    main()
