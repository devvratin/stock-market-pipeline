"""Normalize stress features to 0-1 and combine into a 0-100 Stress Score."""

import math
from pathlib import Path

import pandas as pd
import yaml

from stress.common.logging_setup import get_logger

logger = get_logger(__name__)

DEFAULT_WEIGHTS_PATH = Path("config/stress_weights.yaml")


def load_stress_weights(
    yaml_path: Path = DEFAULT_WEIGHTS_PATH,
) -> tuple[dict[str, float], int, int]:
    """Load feature weights and rolling window settings from YAML."""
    cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    weights: dict[str, float] = {k: float(v) for k, v in cfg["weights"].items()}
    total = sum(weights.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError(f"Stress weights must sum to 1.0, got {total:.6f}")

    window = int(cfg.get("rolling_window_days", 252))
    min_periods = int(cfg.get("min_periods", 60))
    return weights, window, min_periods


def rolling_percentile_rank(
    series: pd.Series,
    window: int = 252,
    min_periods: int = 60,
) -> pd.Series:
    """Compute trailing rolling percentile rank in [0.0, 1.0] without look-ahead."""
    return series.rolling(window=window, min_periods=min_periods).rank(pct=True)


def compute_stress_score(
    df: pd.DataFrame,
    weights: dict[str, float],
    window: int = 252,
    min_periods: int = 60,
) -> pd.DataFrame:
    """Add normalized 0-1 percentile columns and a weighted 0-100 stress_score."""
    out = df.copy()
    weighted_sum = pd.Series(0.0, index=out.index, dtype="float64")

    for feature, weight in weights.items():
        if feature not in out.columns:
            raise KeyError(f"Missing required feature column: {feature}")
        pct_col = f"{feature}_pct"
        out[pct_col] = rolling_percentile_rank(
            out[feature], window=window, min_periods=min_periods
        )
        weighted_sum = weighted_sum + (out[pct_col] * weight)

    out["stress_score"] = (weighted_sum * 100.0).round(2)
    return out