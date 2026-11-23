"""Offline unit tests for daily stress and 30-day sudden-change SQL reports."""

import pandas as pd

from stress.transform.reports import get_daily_stress, get_recent_anomalies


def _write_sample_gold(gold_path) -> None:
    df = pd.DataFrame(
        {
            "symbol": ["RELIANCE", "TCS", "INFY", "RELIANCE"],
            "trade_date": pd.to_datetime(
                ["2026-11-20", "2026-11-20", "2026-11-10", "2026-09-01"]
            ),
            "close": [1300.0, 4100.0, 1850.0, 1250.0],
            "daily_return": [-0.045, 0.005, 0.06, -0.05],
            "volume_spike": [3.2, 1.1, 1.4, 2.9],
            "stress_score": [91.5, 42.0, 78.0, 88.0],
            "is_return_anomaly": [True, False, True, True],
            "is_volume_anomaly": [True, False, False, True],
            "is_anomaly": [True, False, True, True],
            "india_vix_close": [17.5, 17.5, 14.2, 15.0],
        }
    )
    df.to_parquet(gold_path, index=False)


def test_get_daily_stress_for_specific_date(tmp_path):
    gold_path = tmp_path / "stock_stress.parquet"
    _write_sample_gold(gold_path)

    resolved, df = get_daily_stress(target_date="2026-11-20", gold_path=gold_path)

    assert resolved == "2026-11-20"
    assert list(df["symbol"]) == ["RELIANCE", "TCS"]  # highest stress first
    assert df["stress_score"].iloc[0] == 91.5


def test_get_recent_anomalies_filters_last_30_days_date_wise(tmp_path):
    gold_path = tmp_path / "stock_stress.parquet"
    _write_sample_gold(gold_path)

    df = get_recent_anomalies(days=30, gold_path=gold_path)

    # 2026-09-01 is > 30 days before 2026-11-20, so only 2026-11-20 and 2026-11-10 remain
    assert len(df) == 2
    assert list(df["symbol"]) == ["RELIANCE", "INFY"]
    assert df["trigger_reason"].iloc[0] == "Return + Volume"
    assert df["trigger_reason"].iloc[1] == "Return Shock"