import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest BaoStock into an immutable normalized research dataset"
    )
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--coverage-start", required=True)
    parser.add_argument("--coverage-end", required=True)
    parser.parse_args()
    raise SystemExit(
        "DATA_READINESS_BLOCKED: corporate-action normalization and complete "
        "delisting-history validation must be implemented before a dataset may be frozen"
    )


if __name__ == "__main__":
    main()
