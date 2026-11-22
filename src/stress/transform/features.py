"""Pure feature-engineering functions for market stress signals."""

import math

import numpy as np
import pandas as pd


def compute_daily_return(close: pd.Series) -> pd.Series:
    """Simple daily percentage return: (close_t - close_{t-1}) / close_{t-1}."""
    return close.pct_change()


def compute_realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """Rolling sample standard deviation of daily returns."""
    return returns.rolling(window=window).std(ddof=1)


def compute_parkinson_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Rolling Parkinson volatility using daily high/low range."""
    log_hl_sq = np.log(high / low) ** 2
    daily_var = log_hl_sq / (4.0 * math.log(2.0))
    return np.sqrt(daily_var.rolling(window=window).mean())


def compute_garman_klass_volatility(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Rolling Garman-Klass volatility using full OHLC prices."""
    log_hl_sq = np.log(high / low) ** 2
    log_co_sq = np.log(close / open_) ** 2
    daily_var = 0.5 * log_hl_sq - (2.0 * math.log(2.0) - 1.0) * log_co_sq
    rolling_var = daily_var.rolling(window=window).mean().clip(lower=0.0)
    return np.sqrt(rolling_var)


def compute_volume_spike(volume: pd.Series, window: int = 20) -> pd.Series:
    """Volume divided by the prior window average (shifted 1 day to prevent look-ahead)."""
    prior_avg = volume.shift(1).rolling(window=window).mean()
    return volume / prior_avg.replace(0, np.nan)


def compute_spread_proxy(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> pd.Series:
    """Range-based spread proxy: (high - low) / close."""
    return (high - low) / close


def compute_anomaly_flags(
    returns: pd.Series,
    volume_spike: pd.Series,
    window: int = 20,
    return_sigma: float = 3.0,
    volume_threshold: float = 2.5,
) -> pd.DataFrame:
    """Flag extreme return shocks or volume spikes (using shifted std to avoid look-ahead)."""
    prior_std = returns.shift(1).rolling(window=window).std(ddof=1)
    is_return_anomaly = (returns.abs() > (return_sigma * prior_std)).fillna(False)
    is_volume_anomaly = (volume_spike > volume_threshold).fillna(False)
    return pd.DataFrame(
        {
            "is_return_anomaly": is_return_anomaly,
            "is_volume_anomaly": is_volume_anomaly,
            "is_anomaly": is_return_anomaly | is_volume_anomaly,
        },
        index=returns.index,
    )


def add_all_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Return a copy of a sorted Silver DataFrame enriched with all Gold stress features."""
    out = df.copy()
    out["daily_return"] = compute_daily_return(out["close"])
    out["realized_vol"] = compute_realized_volatility(out["daily_return"], window=window)
    out["parkinson_vol"] = compute_parkinson_volatility(
        out["high"], out["low"], window=window
    )
    out["garman_klass_vol"] = compute_garman_klass_volatility(
        out["open"], out["high"], out["low"], out["close"], window=window
    )
    out["volume_spike"] = compute_volume_spike(out["volume"], window=window)
    out["spread_proxy"] = compute_spread_proxy(out["high"], out["low"], out["close"])

    flags = compute_anomaly_flags(
        out["daily_return"], out["volume_spike"], window=window
    )
    out["is_return_anomaly"] = flags["is_return_anomaly"]
    out["is_volume_anomaly"] = flags["is_volume_anomaly"]
    out["is_anomaly"] = flags["is_anomaly"]
    return out