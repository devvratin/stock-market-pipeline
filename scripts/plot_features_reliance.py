"""Visualize all Phase 7 Gold features for RELIANCE in a 4-panel chart."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from stress.common import config
from stress.transform.features import add_all_features


def main() -> None:
    silver_path = config.SILVER_DIR / "candles_daily" / "symbol=RELIANCE" / "data.parquet"
    df = pd.read_parquet(silver_path)
    feat = add_all_features(df, window=20)

    fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)

    # Panel 1: Close Price + Anomaly Markers
    axes[0].plot(feat["trade_date"], feat["close"], color="#1f77b4", linewidth=1.2, label="Close")
    anomalies = feat[feat["is_anomaly"]]
    axes[0].scatter(
        anomalies["trade_date"],
        anomalies["close"],
        color="red",
        s=18,
        zorder=3,
        label=f"Anomaly ({len(anomalies)} days)",
    )
    axes[0].set_title("RELIANCE: Phase 7 Stress Features Overview")
    axes[0].set_ylabel("Close (INR)")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)

    # Panel 2: Three Volatility Measures Compared
    axes[1].plot(feat["trade_date"], feat["realized_vol"], label="Realized Vol (20d)", linewidth=1.1)
    axes[1].plot(feat["trade_date"], feat["parkinson_vol"], label="Parkinson Vol (20d)", linewidth=1.1)
    axes[1].plot(
        feat["trade_date"],
        feat["garman_klass_vol"],
        label="Garman-Klass Vol (20d)",
        linewidth=1.1,
    )
    axes[1].set_ylabel("Daily Volatility")
    axes[1].legend(loc="upper left")
    axes[1].grid(alpha=0.3)

    # Panel 3: Volume Spike vs 2.5x Threshold
    axes[2].bar(feat["trade_date"], feat["volume_spike"], width=2, color="#6c757d", alpha=0.7)
    axes[2].axhline(2.5, color="red", linestyle="--", linewidth=1.0, label="Anomaly threshold (2.5x)")
    axes[2].set_ylabel("Volume Spike (x)")
    axes[2].legend(loc="upper left")
    axes[2].grid(alpha=0.3)

    # Panel 4: Spread Proxy = (High - Low) / Close
    axes[3].plot(
        feat["trade_date"],
        feat["spread_proxy"] * 100,
        color="#d95f02",
        linewidth=0.9,
        label="(High - Low) / Close (%)",
    )
    axes[3].set_ylabel("Intraday Range (%)")
    axes[3].set_xlabel("Date")
    axes[3].legend(loc="upper left")
    axes[3].grid(alpha=0.3)

    out_path = Path("docs/reliance_features.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Saved feature visualization to: {out_path}")


if __name__ == "__main__":
    main()