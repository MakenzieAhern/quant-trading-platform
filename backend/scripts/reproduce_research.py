import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce a persisted research run")
    parser.add_argument("--run-id", required=True)
    parser.parse_args()
    raise SystemExit(
        "RESEARCH_RUN_NOT_COMPLETED: persisted completed research results are not yet available"
    )


if __name__ == "__main__":
    main()
