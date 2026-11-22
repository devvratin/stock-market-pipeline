"""Hand-verified unit tests for Phase 7 Gold feature functions."""

import math

import pandas as pd
import pytest

from stress.transform.features import (
    add_all_features,
    compute_anomaly_flags,
    compute_daily_return,
    compute_garman_klass_volatility,
    compute_parkinson_volatility,
    compute_realized_volatility,
    compute_spread_proxy,
    compute_volume_spike,
)


def test_daily_return_and_realized_volatility():
    # Close: 100 -> 110 (+10%) -> 99 (-10%)
    close = pd.Series([100.0, 110.0, 99.0])
    returns = compute_daily_return(close)

    assert pd.isna(returns.iloc[0])
    assert returns.iloc[1] == pytest.approx(0.10)
    assert returns.iloc[2] == pytest.approx(-0.10)

    # Sample std of [0.10, -0.10] = sqrt(((0.1)^2 + (-0.1)^2) / 1) = sqrt(0.02)
    vol = compute_realized_volatility(returns, window=2)
    assert vol.iloc[2] == pytest.approx(math.sqrt(0.02))


def test_parkinson_volatility():
    # High=200, Low=100 -> ln(H/L) = ln(2)
    # Daily variance = (ln 2)^2 / (4 * ln 2) = ln(2) / 4 -> vol = sqrt(ln(2) / 4)
    high = pd.Series([200.0])
    low = pd.Series([100.0])
    expected = math.sqrt(math.log(2.0) / 4.0)

    vol = compute_parkinson_volatility(high, low, window=1)
    assert vol.iloc[0] == pytest.approx(expected)


def test_garman_klass_volatility():
    # Open=100, Close=100 -> ln(C/O) = 0
    # High=200, Low=100 -> ln(H/L) = ln(2)
    # Daily variance = 0.5 * (ln 2)^2 -> vol = sqrt(0.5) * ln(2)
    open_ = pd.Series([100.0])
    high = pd.Series([200.0])
    low = pd.Series([100.0])
    close = pd.Series([100.0])
    expected = math.sqrt(0.5) * math.log(2.0)

    vol = compute_garman_klass_volatility(open_, high, low, close, window=1)
    assert vol.iloc[0] == pytest.approx(expected)


def test_volume_spike_uses_shifted_baseline():
    # Volumes: [100, 300, 600] with window=2
    # At index 2, prior 2-day avg = (100 + 300) / 2 = 200 -> spike = 600 / 200 = 3.0
    volume = pd.Series([100, 300, 600])
    spike = compute_volume_spike(volume, window=2)

    assert pd.isna(spike.iloc[1])
    assert spike.iloc[2] == pytest.approx(3.0)


def test_spread_proxy():
    # (110 - 100) / 100 = 0.10
    spread = compute_spread_proxy(
        high=pd.Series([110.0]),
        low=pd.Series([100.0]),
        close=pd.Series([100.0]),
    )
    assert spread.iloc[0] == pytest.approx(0.10)


def test_anomaly_flags():
    # Small stable returns followed by a huge +20% jump and a 3.0x volume spike
    returns = pd.Series([0.01, -0.01, 0.01, -0.01, 0.20])
    vol_spike = pd.Series([1.0, 1.0, 1.0, 1.0, 3.0])

    flags = compute_anomaly_flags(
        returns, vol_spike, window=3, return_sigma=3.0, volume_threshold=2.5
    )

    assert bool(flags["is_return_anomaly"].iloc[4]) is True
    assert bool(flags["is_volume_anomaly"].iloc[4]) is True
    assert bool(flags["is_anomaly"].iloc[4]) is True
    assert bool(flags["is_anomaly"].iloc[3]) is False


def test_add_all_features_adds_expected_columns():
    df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 101.0, 105.0],
            "high": [105.0, 106.0, 104.0, 112.0],
            "low": [98.0, 100.0, 99.0, 103.0],
            "close": [102.0, 101.0, 105.0, 110.0],
            "volume": [1000, 1100, 1050, 4000],
        }
    )
    enriched = add_all_features(df, window=2)

    expected_cols = {
        "daily_return",
        "realized_vol",
        "parkinson_vol",
        "garman_klass_vol",
        "volume_spike",
        "spread_proxy",
        "is_return_anomaly",
        "is_volume_anomaly",
        "is_anomaly",
    }
    assert expected_cols.issubset(set(enriched.columns))