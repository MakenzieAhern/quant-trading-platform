import argparse
from pathlib import Path

from app.data.catalog.repository import LocalDatasetCatalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a frozen research dataset")
    parser.add_argument("dataset_id")
    parser.add_argument("--root", type=Path, default=Path("data/research"))
    args = parser.parse_args()
    manifest = LocalDatasetCatalog(args.root).get(args.dataset_id)
    print(f"verified {manifest.dataset_id} {manifest.canonical_sha256}")


if __name__ == "__main__":
    main()
