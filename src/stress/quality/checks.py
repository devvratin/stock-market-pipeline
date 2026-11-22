"""Data quality checks for daily OHLCV market data."""

from dataclasses import dataclass

import pandas as pd

OHLCV_COLS = ["open", "high", "low", "close", "volume"]
PRICE_COLS = ["open", "high", "low", "close"]


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a single data quality check."""

    name: str
    passed: bool
    failed_rows: int
    details: str


def check_no_nulls(df: pd.DataFrame) -> CheckResult:
    """Ensure OHLCV columns contain no null/NaN values."""
    bad_mask = df[OHLCV_COLS].isna().any(axis=1)
    failed = int(bad_mask.sum())
    return CheckResult(
        name="no_nulls_ohlcv",
        passed=failed == 0,
        failed_rows=failed,
        details="All OHLCV values present"
        if failed == 0
        else f"Found {failed} row(s) with null OHLCV values",
    )


def check_ohlc_logic(df: pd.DataFrame) -> CheckResult:
    """Ensure high >= low, high >= open/close, and low <= open/close."""
    valid = (
        (df["high"] >= df["low"])
        & (df["high"] >= df["open"])
        & (df["high"] >= df["close"])
        & (df["low"] <= df["open"])
        & (df["low"] <= df["close"])
    )
    failed = int((~valid).sum())
    return CheckResult(
        name="ohlc_logic",
        passed=failed == 0,
        failed_rows=failed,
        details="All OHLC price bounds valid"
        if failed == 0
        else f"Found {failed} row(s) violating OHLC high/low bounds",
    )


def check_positive_prices_and_volume(df: pd.DataFrame) -> CheckResult:
    """Ensure all OHLC prices are > 0 and volume is >= 0."""
    prices_ok = (df[PRICE_COLS] > 0).all(axis=1)
    volume_ok = df["volume"] >= 0
    failed = int((~(prices_ok & volume_ok)).sum())
    return CheckResult(
        name="positive_prices_and_volume",
        passed=failed == 0,
        failed_rows=failed,
        details="All prices > 0 and volume >= 0"
        if failed == 0
        else f"Found {failed} row(s) with non-positive price or negative volume",
    )


def check_no_duplicate_dates(df: pd.DataFrame) -> CheckResult:
    """Ensure trade_date has no duplicate entries."""
    failed = int(df["trade_date"].duplicated().sum())
    return CheckResult(
        name="no_duplicate_dates",
        passed=failed == 0,
        failed_rows=failed,
        details="No duplicate trade_date values"
        if failed == 0
        else f"Found {failed} duplicate trade_date row(s)",
    )


def check_no_unexpected_gaps(
    df: pd.DataFrame,
    max_calendar_gap_days: int = 7,
) -> CheckResult:
    """Flag gaps larger than max_calendar_gap_days (allows weekends + long holidays)."""
    dates = pd.to_datetime(df["trade_date"]).sort_values()
    gaps = dates.diff().dt.days
    bad_gaps = gaps[gaps > max_calendar_gap_days]
    failed = int(len(bad_gaps))
    max_gap = int(gaps.max()) if len(gaps.dropna()) > 0 else 0
    return CheckResult(
        name="no_unexpected_gaps",
        passed=failed == 0,
        failed_rows=failed,
        details=f"Max calendar gap is {max_gap} day(s)"
        if failed == 0
        else (
            f"Found {failed} gap(s) > {max_calendar_gap_days} days "
            f"(max gap: {max_gap} days)"
        ),
    )


def run_all_checks(
    df: pd.DataFrame,
    max_calendar_gap_days: int = 7,
) -> list[CheckResult]:
    """Run all five OHLCV data quality checks and return their results."""
    return [
        check_no_nulls(df),
        check_ohlc_logic(df),
        check_positive_prices_and_volume(df),
        check_no_duplicate_dates(df),
        check_no_unexpected_gaps(df, max_calendar_gap_days=max_calendar_gap_days),
    ]