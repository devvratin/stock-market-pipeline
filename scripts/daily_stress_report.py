"""CLI: Print daily stress scores for all 50 Nifty 50 stocks on a given date."""

import argparse

from stress.transform.reports import get_daily_stress


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show daily stress scores for all 50 Nifty 50 companies."
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Trading date in YYYY-MM-DD format (defaults to latest available date)",
    )
    args = parser.parse_args()

    resolved_date, df = get_daily_stress(target_date=args.date)

    if df.empty:
        print(
            f"No trading data found for {resolved_date} "
            "(it may be a weekend or NSE market holiday)."
        )
        return

    print(f"\nNifty 50 Daily Stress Report — {resolved_date} ({len(df)} stocks):\n")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()