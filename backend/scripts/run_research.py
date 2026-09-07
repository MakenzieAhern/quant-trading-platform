import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a research run from registered IDs")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument(
        "--strategy-id",
        default="cn_a_cross_sectional_momentum_low_vol_v1",
        choices=("cn_a_cross_sectional_momentum_low_vol_v1",),
    )
    parser.add_argument("--period", choices=("DEVELOPMENT", "VALIDATION"), required=True)
    parser.parse_args()
    raise SystemExit(
        "DATA_READINESS_BLOCKED: no A-share dataset has passed the immutable readiness gate"
    )


if __name__ == "__main__":
    main()
