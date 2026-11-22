"""Sanity check: compute RELIANCE stress score, query peak dates via SQL, and save a plot."""

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

from stress.common import config
from stress.transform.features import add_all_features
from stress.transform.scoring import compute_stress_score, load_stress_weights


def main() -> None:
    silver_path = config.SILVER_DIR / "candles_daily" / "symbol=RELIANCE" / "data.parquet"
    df = pd.read_parquet(silver_path)

    weights, window, min_periods = load_stress_weights()
    featured = add_all_features(df, window=20)
    scored = compute_stress_score(
        featured, weights=weights, window=window, min_periods=min_periods
    )

    # Use DuckDB SQL to inspect top stress days and key historical events
    top_days = duckdb.sql(
        """
        SELECT
            trade_date::DATE AS trade_date,
            ROUND(close, 2) AS close,
            ROUND(daily_return * 100, 2) AS return_pct,
            stress_score,
            is_anomaly
        FROM scored
        WHERE stress_score IS NOT NULL
        ORDER BY stress_score DESC
        LIMIT 10
        """
    ).df()
    print("\nTop 10 highest-stress days for RELIANCE:")
    print(top_days.to_string(index=False))

    # Plot stress score over time
    plot_df = scored.dropna(subset=["stress_score"])
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(plot_df["trade_date"], plot_df["stress_score"], linewidth=1.2, label="Stress Score")

    anomalies = plot_df[plot_df["is_anomaly"]]
    ax.scatter(
        anomalies["trade_date"],
        anomalies["stress_score"],
        color="red",
        s=18,
        zorder=3,
        label="Anomaly",
    )

    ax.set_title("RELIANCE Daily Market Stress Score (0-100)")
    ax.set_ylabel("Stress Score")
    ax.set_ylim(0, 105)
    ax.grid(alpha=0.3)
    ax.legend()

    out_img = Path("docs/reliance_stress_sanity.png")
    fig.tight_layout()
    fig.savefig(out_img, dpi=150)
    print(f"\nSaved sanity-check chart to: {out_img}")


if __name__ == "__main__":
    main()