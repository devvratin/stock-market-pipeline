"""Unit tests for Phase 5 data quality checks using deliberately broken DataFrames."""

import pandas as pd

from stress.quality.checks import (
    check_no_duplicate_dates,
    check_no_nulls,
    check_no_unexpected_gaps,
    check_ohlc_logic,
    check_positive_prices_and_volume,
    run_all_checks,
)


def _valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": ["2026-11-18", "2026-11-19", "2026-11-20"],
            "open": [100.0, 102.0, 104.0],
            "high": [105.0, 106.0, 108.0],
            "low": [99.0, 101.0, 103.0],
            "close": [102.0, 104.0, 107.0],
            "volume": [1000, 1200, 1500],
        }
    )


def test_valid_dataframe_passes_all_checks():
    results = run_all_checks(_valid_df())
    assert len(results) == 5
    assert all(r.passed for r in results)


def test_check_no_nulls_catches_missing_value():
    df = _valid_df()
    df.loc[1, "close"] = None

    result = check_no_nulls(df)
    assert result.passed is False
    assert result.failed_rows == 1


def test_check_ohlc_logic_catches_inverted_high_low():
    df = _valid_df()
    df.loc[0, "high"] = 95.0  # lower than low (99.0) and open (100.0)

    result = check_ohlc_logic(df)
    assert result.passed is False
    assert result.failed_rows == 1


def test_check_positive_prices_and_volume_catches_bad_values():
    df = _valid_df()
    df.loc[0, "open"] = 0.0
    df.loc[2, "volume"] = -50

    result = check_positive_prices_and_volume(df)
    assert result.passed is False
    assert result.failed_rows == 2


def test_check_no_duplicate_dates_catches_duplicate():
    df = _valid_df()
    df.loc[2, "trade_date"] = "2026-11-19"

    result = check_no_duplicate_dates(df)
    assert result.passed is False
    assert result.failed_rows == 1


def test_check_no_unexpected_gaps_catches_missing_weeks():
    df = _valid_df()
    df.loc[2, "trade_date"] = "2026-12-05"  # 16-day gap from 2026-11-19

    result = check_no_unexpected_gaps(df, max_calendar_gap_days=7)
    assert result.passed is False
    assert result.failed_rows == 1