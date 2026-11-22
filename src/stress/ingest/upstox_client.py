"""Upstox Historical Candle V3 client and Bronze writer."""

import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

from stress.common import config
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST

logger = get_logger(__name__)

HISTORICAL_V3_BASE = "https://api.upstox.com/v3/historical-candle"


def get_daily_candles(
    instrument_key: str,
    from_date: str,
    to_date: str,
    access_token: str | None = None,
    max_retries: int = 3,
    sleep_seconds: float = 0.25,
) -> dict:
    """Fetch daily historical candles from Upstox V3 with retries and rate-limit sleep."""
    encoded_key = quote(instrument_key, safe="")
    # Upstox V3 path order: /{instrument_key}/{unit}/{interval}/{to_date}/{from_date}
    url = f"{HISTORICAL_V3_BASE}/{encoded_key}/days/1/{to_date}/{from_date}"

    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Fetching daily candles for %s (%s to %s) [attempt %d/%d]",
                instrument_key,
                from_date,
                to_date,
                attempt,
                max_retries,
            )
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            logger.warning("Attempt %d failed for %s: %s", attempt, instrument_key, exc)
            if attempt < max_retries:
                time.sleep(sleep_seconds * attempt)

    raise RuntimeError(
        f"Failed to fetch candles for {instrument_key} after {max_retries} attempts"
    ) from last_error


def save_bronze_candles(
    symbol: str,
    payload: dict,
    run_date: str | None = None,
    bronze_dir: Path = config.BRONZE_DIR,
) -> Path:
    """Save the raw Upstox JSON response untouched into Hive-partitioned Bronze storage."""
    date_str = run_date or datetime.now(IST).date().isoformat()
    out_dir = bronze_dir / "candles_daily" / f"symbol={symbol.upper()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{date_str}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    candle_count = len(payload.get("data", {}).get("candles", []))
    logger.info("Saved %d raw candles to %s", candle_count, out_path)
    return out_path