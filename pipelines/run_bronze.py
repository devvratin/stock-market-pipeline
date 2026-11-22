"""CLI runner to ingest raw daily candles for a single NSE symbol into Bronze."""

import argparse
from datetime import datetime

from stress.auth.upstox_auth import get_token
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST
from stress.ingest.instruments import (
    build_equity_map,
    download_instruments,
    load_instruments,
    symbol_to_key,
)
from stress.ingest.upstox_client import get_daily_candles, save_bronze_candles

logger = get_logger(__name__)


def main() -> None:
    today_ist = datetime.now(IST).date().isoformat()
    parser = argparse.ArgumentParser(description="Ingest raw daily candles into Bronze.")
    parser.add_argument("symbol", help="NSE stock symbol (e.g. RELIANCE)")
    parser.add_argument("--from-date", default="2020-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--to-date", default=today_ist, help="End date YYYY-MM-DD")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    instruments_path = download_instruments()
    equity_map = build_equity_map(load_instruments(instruments_path))

    instrument_key = symbol_to_key(symbol, equity_map)
    if not instrument_key:
        raise SystemExit(f"Could not resolve instrument_key for {symbol}")

    token = get_token()
    payload = get_daily_candles(
        instrument_key=instrument_key,
        from_date=args.from_date,
        to_date=args.to_date,
        access_token=token,
    )
    out_path = save_bronze_candles(symbol=symbol, payload=payload, run_date=args.to_date)
    print(f"Done! Raw Bronze file saved at: {out_path}")


if __name__ == "__main__":
    main()