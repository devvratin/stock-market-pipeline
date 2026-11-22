"""Offline unit tests for Phase 6 Silver transformation."""

import json
from pathlib import Path

import pandas as pd

from stress.transform.silver import build_silver_for_symbol, raw_json_to_silver_df

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_candles.json"


def test_raw_json_to_silver_df_sorts_deduplicates_and_checks():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # Add a deliberate duplicate candle to verify deduplication
    payload["data"]["candles"].append(payload["data"]["candles"][0])

    df, results = raw_json_to_silver_df(payload, symbol="reliance")

    assert len(df) == 2
    assert list(df["symbol"]) == ["RELIANCE", "RELIANCE"]
    assert df["trade_date"].is_monotonic_increasing
    assert str(df["timestamp"].dt.tz) == "Asia/Kolkata"
    assert df["close"].dtype == "float64"
    assert df["volume"].dtype == "int64"
    assert all(r.passed for r in results)


def test_build_silver_for_symbol_writes_readable_parquet(tmp_path):
    bronze_dir = tmp_path / "bronze"
    silver_dir = tmp_path / "silver"
    symbol_dir = bronze_dir / "candles_daily" / "symbol=RELIANCE"
    symbol_dir.mkdir(parents=True)
    (symbol_dir / "2026-11-20.json").write_text(
        FIXTURE_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    out_path, results = build_silver_for_symbol(
        "RELIANCE",
        bronze_dir=bronze_dir,
        silver_dir=silver_dir,
    )

    assert out_path.exists()
    loaded = pd.read_parquet(out_path)
    assert len(loaded) == 2
    assert all(r.passed for r in results)