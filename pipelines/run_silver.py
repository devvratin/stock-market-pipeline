"""CLI runner to transform a symbol's Bronze JSON into Silver Parquet and verify via SQL."""

import argparse

import duckdb

from stress.transform.silver import build_silver_for_symbol


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Silver Parquet from Bronze JSON.")
    parser.add_argument("symbol", help="NSE stock symbol (e.g. RELIANCE)")
    args = parser.parse_args()

    out_path, results = build_silver_for_symbol(args.symbol)

    # Quick SQL check directly on the Parquet file using DuckDB
    summary = duckdb.sql(
        f"""
        SELECT
            symbol,
            COUNT(*) AS total_rows,
            MIN(trade_date)::DATE AS first_date,
            MAX(trade_date)::DATE AS last_date
        FROM read_parquet('{out_path.as_posix()}')
        GROUP BY symbol
        """
    ).df()

    print("\nSilver Parquet summary (via DuckDB SQL):")
    print(summary.to_string(index=False))

    failed = [r for r in results if not r.passed]
    print(f"\nQuality checks passed: {len(results) - len(failed)}/{len(results)}")
    for r in failed:
        print(f"  WARNING - {r.name}: {r.details}")


if __name__ == "__main__":
    main()