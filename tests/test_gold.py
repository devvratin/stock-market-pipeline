"""Offline unit tests for Phase 9 Gold table aggregation and India VIX SQL join."""

import pandas as pd

from stress.transform.gold import build_gold_tables


def _write_silver(silver_dir, symbol: str, closes: list[float], volumes: list[int]) -> None:
    out_dir = silver_dir / "candles_daily" / f"symbol={symbol}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range("2026-11-10", periods=len(closes), freq="B")
    df = pd.DataFrame(
        {
            "symbol": symbol,
            "trade_date": dates,
            "timestamp": dates,
            "open": closes,
            "high": [c * 1.02 for c in closes],
            "low": [c * 0.98 for c in closes],
            "close": closes,
            "volume": volumes,
        }
    )
    df.to_parquet(out_dir / "data.parquet", index=False)


def test_build_gold_tables_joins_vix_and_aggregates_index(tmp_path):
    silver_dir = tmp_path / "silver"
    gold_dir = tmp_path / "gold"

    _write_silver(silver_dir, "RELIANCE", [100, 102, 105, 101, 110], [100, 110, 120, 130, 400])
    _write_silver(silver_dir, "TCS", [200, 202, 204, 206, 208], [200, 210, 205, 215, 220])
    _write_silver(silver_dir, "INDIA_VIX", [14.0, 14.5, 15.0, 16.0, 18.5], [0, 0, 0, 0, 0])

    stock_path, index_path = build_gold_tables(
        silver_dir=silver_dir,
        gold_dir=gold_dir,
        feature_window=2,
        score_window=3,
        min_periods=2,
    )

    stock_df = pd.read_parquet(stock_path)
    index_df = pd.read_parquet(index_path)

    assert set(stock_df["symbol"]) == {"RELIANCE", "TCS"}
    assert "india_vix_close" in stock_df.columns
    assert stock_df["india_vix_close"].notna().all()

    assert len(index_df) > 0
    assert (index_df["stock_count"] == 2).all()
    assert index_df["index_stress_score"].between(0.0, 100.0).all()
    assert index_df["india_vix_close"].iloc[-1] == 18.5