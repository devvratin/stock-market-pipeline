"""Bronze JSON -> Silver Parquet transformation with quality validation."""

import json
from pathlib import Path

import pandas as pd

from stress.common import config
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST
from stress.quality.checks import CheckResult, run_all_checks

logger = get_logger(__name__)

RAW_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "oi"]


def raw_json_to_silver_df(
    payload: dict,
    symbol: str,
) -> tuple[pd.DataFrame, list[CheckResult]]:
    """Convert raw Upstox candle JSON to a typed, sorted, deduplicated DataFrame."""
    candles = payload.get("data", {}).get("candles", [])
    if not candles:
        raise ValueError(f"No candles found in Bronze payload for {symbol}")

    df = pd.DataFrame(candles, columns=RAW_COLUMNS)
    df["symbol"] = symbol.upper()

    # Parse timestamps and normalize to IST
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(IST)
    df["trade_date"] = pd.to_datetime(df["timestamp"].dt.date)

    # Enforce numeric types
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")

    # Select clean Silver schema
    silver_cols = ["symbol", "trade_date", "timestamp", "open", "high", "low", "close", "volume"]
    df = df[silver_cols]

    # Sort ascending by trade_date and drop any duplicate dates
    df = df.sort_values("trade_date", ascending=True).reset_index(drop=True)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["trade_date"], keep="last").reset_index(drop=True)
    dropped = before_dedup - len(df)
    if dropped > 0:
        logger.warning("Dropped %d duplicate trade_date row(s) for %s", dropped, symbol)

    # Run Phase 5 data quality checks and log results
    results = run_all_checks(df)
    for res in results:
        if res.passed:
            logger.info("[%s] PASS %s: %s", symbol, res.name, res.details)
        else:
            logger.warning("[%s] FAIL %s: %s", symbol, res.name, res.details)

    return df, results


def build_silver_for_symbol(
    symbol: str,
    bronze_dir: Path = config.BRONZE_DIR,
    silver_dir: Path = config.SILVER_DIR,
) -> tuple[Path, list[CheckResult]]:
    """Load the latest Bronze JSON for a symbol and write clean Silver Parquet."""
    sym = symbol.upper()
    bronze_symbol_dir = bronze_dir / "candles_daily" / f"symbol={sym}"
    json_files = sorted(bronze_symbol_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No Bronze JSON files found in {bronze_symbol_dir}")

    latest_file = json_files[-1]
    logger.info("Reading Bronze file: %s", latest_file)
    payload = json.loads(latest_file.read_text(encoding="utf-8"))

    df, results = raw_json_to_silver_df(payload, symbol=sym)

    out_dir = silver_dir / "candles_daily" / f"symbol={sym}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.parquet"
    df.to_parquet(out_path, index=False)
    logger.info("Wrote %d Silver rows to %s", len(df), out_path)
    return out_path, results