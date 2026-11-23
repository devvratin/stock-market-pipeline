"""CLI: Print last 30 days of Nifty 50 stocks with sudden return or volume changes, date-wise."""

import argparse

from stress.transform.reports import get_recent_anomalies


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show stocks with sudden changes (anomalies) over the last N days."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of trailing calendar days to inspect (default: 30)",
    )
    args = parser.parse_args()

    df = get_recent_anomalies(days=args.days)

    if df.empty:
        print(f"No sudden-change anomalies detected in the last {args.days} days.")
        return

    print(
        f"\nNifty 50 Sudden Changes — Last {args.days} Days "
        f"({len(df)} events, ordered date-wise):\n"
    )
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()