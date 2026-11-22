"""End-to-end runner: Bronze -> Silver -> Gold for all 50 Nifty 50 stocks + India VIX."""

import argparse
from datetime import datetime

import duckdb

from stress.auth.upstox_auth import get_token
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST
from stress.ingest.instruments import (
    build_equity_map,
    download_instruments,
    find_india_vix_key,
    load_instruments,
    load_nifty50_symbols,
    resolve_nifty50,
)
from stress.ingest.upstox_client import get_daily_candles, save_bronze_candles
from stress.transform.gold import VIX_SYMBOL, build_gold_tables
from stress.transform.silver import build_silver_for_symbol

logger = get_logger(__name__)


def main() -> None:
    today_ist = datetime.now(IST).date().isoformat()
    parser = argparse.ArgumentParser(description="Run full Nifty 50 + India VIX pipeline.")
    parser.add_argument("--from-date", default="2020-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--to-date", default=today_ist, help="End date YYYY-MM-DD")
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip API calls and rebuild Gold directly from existing Silver Parquet files",
    )
    args = parser.parse_args()

    if not args.skip_ingest:
        instruments_path = download_instruments()
        instruments = load_instruments(instruments_path)
        equity_map = build_equity_map(instruments)

        symbols = load_nifty50_symbols()
        resolved, missing = resolve_nifty50(symbols, equity_map)
        if missing:
            logger.warning("Skipping unresolved symbols: %s", missing)

        # Add India VIX to the ingestion list
        vix_key = find_india_vix_key(instruments)
        if vix_key:
            resolved[VIX_SYMBOL] = vix_key

        token = get_token()
        failed_symbols: list[str] = []

        for idx, (sym, key) in enumerate(resolved.items(), start=1):
            try:
                logger.info("[%d/%d] Processing %s (%s)", idx, len(resolved), sym, key)
                payload = get_daily_candles(
                    instrument_key=key,
                    from_date=args.from_date,
                    to_date=args.to_date,
                    access_token=token,
                )
                save_bronze_candles(symbol=sym, payload=payload, run_date=args.to_date)
                build_silver_for_symbol(symbol=sym)
            except Exception as exc:
                logger.error("Failed processing %s: %s", sym, exc)
                failed_symbols.append(sym)

        logger.info(
            "Bronze + Silver complete: %d succeeded, %d failed.",
            len(resolved) - len(failed_symbols),
            len(failed_symbols),
        )
        if failed_symbols:
            logger.warning("Failed symbols: %s", failed_symbols)

    # Build combined Gold tables via DuckDB SQL
    stock_gold_path, index_gold_path = build_gold_tables()

    # Print quick SQL verification of the latest 5 days of Nifty 50 Index Stress
    latest = duckdb.sql(
        f"""
        SELECT
            trade_date::DATE AS trade_date,
            index_stress_score,
            max_stock_stress,
            stocks_in_anomaly,
            stock_count,
            ROUND(india_vix_close, 2) AS india_vix
        FROM read_parquet('{index_gold_path.as_posix()}')
        ORDER BY trade_date DESC
        LIMIT 5
        """
    ).df()
    print("\nLatest 5 trading days — Nifty 50 Index Stress (Gold):")
    print(latest.to_string(index=False))
    print(f"\nGold tables saved:\n  - {stock_gold_path}\n  - {index_gold_path}")


if __name__ == "__main__":
    main()