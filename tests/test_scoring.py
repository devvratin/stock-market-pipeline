"""Unit tests for Phase 8 stress score normalization and weighting."""

import pandas as pd
import pytest

from stress.transform.scoring import (
    compute_stress_score,
    load_stress_weights,
    rolling_percentile_rank,
)


def test_load_stress_weights_sums_to_one():
    weights, window, min_periods = load_stress_weights()
    assert sum(weights.values()) == pytest.approx(1.0)
    assert window == 252
    assert min_periods == 60


def test_rolling_percentile_rank_bounds():
    # Strictly increasing series -> last value is always the highest (rank = 1.0)
    s = pd.Series([10.0, 20.0, 30.0, 40.0])
    ranked = rolling_percentile_rank(s, window=4, min_periods=2)

    assert pd.isna(ranked.iloc[0])
    assert ranked.iloc[1] == pytest.approx(1.0)
    assert ranked.iloc[3] == pytest.approx(1.0)
    assert ranked.dropna().between(0.0, 1.0).all()


def test_compute_stress_score_weighted_math():
    # Feature A strictly rises (rank=1.0 on last row)
    # Feature B strictly falls (rank=0.25 on last row of 4)
    # Weights 0.6 and 0.4 -> expected score = 100 * (0.6 * 1.0 + 0.4 * 0.25) = 70.0
    df = pd.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0],
            "feat_b": [40.0, 30.0, 20.0, 10.0],
        }
    )
    weights = {"feat_a": 0.6, "feat_b": 0.4}

    scored = compute_stress_score(df, weights=weights, window=4, min_periods=4)

    assert scored["stress_score"].iloc[3] == pytest.approx(70.0)
    assert scored["stress_score"].dropna().between(0.0, 100.0).all()