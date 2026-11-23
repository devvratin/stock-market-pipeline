"""Streamlit dashboard for the Nifty 50 Market Stress Monitor."""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from stress.common import config
from stress.transform.reports import get_daily_stress, get_recent_anomalies

st.set_page_config(page_title="Nifty 50 Market Stress Monitor", layout="wide")
st.title("Nifty 50 Market Stress Monitor")
st.caption("Medallion Pipeline: Upstox API -> Bronze JSON -> Silver Parquet -> DuckDB SQL Gold")

index_path = config.GOLD_DIR / "nifty50_stress.parquet"
stock_path = config.GOLD_DIR / "stock_stress.parquet"

if not index_path.exists() or not stock_path.exists():
    st.error("Gold tables not found. Run `uv run python pipelines/run_all.py` first.")
    st.stop()

index_df = pd.read_parquet(index_path).sort_values("trade_date")
stock_df = pd.read_parquet(stock_path).sort_values(["symbol", "trade_date"])

# --- Top KPI Row ---
latest = index_df.iloc[-1]
latest_date = pd.to_datetime(latest["trade_date"]).date()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Trading Date", str(latest_date))
col2.metric("Nifty 50 Stress Score", f"{latest['index_stress_score']:.1f} / 100")
vix_val = f"{latest['india_vix_close']:.2f}" if pd.notna(latest["india_vix_close"]) else "N/A"
col3.metric("India VIX", vix_val)
col4.metric("Stocks in Anomaly", f"{int(latest['stocks_in_anomaly'])} / {int(latest['stock_count'])}")

# --- 1. Nifty 50 Index Stress Over Time ---
st.subheader("Nifty 50 Index Stress Score Over Time")
fig_idx, ax_idx = plt.subplots(figsize=(12, 3.8))
ax_idx.plot(
    index_df["trade_date"],
    index_df["index_stress_score"],
    color="#1f77b4",
    linewidth=1.3,
    label="Index Stress Score (0-100)",
)
ax_idx.axhline(75, color="red", linestyle="--", linewidth=0.9, label="High Stress (75)")
ax_idx.set_ylabel("Stress Score")
ax_idx.set_ylim(0, 105)
ax_idx.grid(alpha=0.3)
ax_idx.legend(loc="upper left")
fig_idx.tight_layout()
st.pyplot(fig_idx)

# --- 2. Top-10 Most Stressed Stocks for Any Date ---
st.subheader("Top 10 Most Stressed Nifty 50 Stocks")
available_dates = sorted(stock_df["trade_date"].dt.date.unique(), reverse=True)
selected_date = st.selectbox("Select trading date", options=available_dates, index=0)

_, daily_df = get_daily_stress(target_date=str(selected_date), gold_path=stock_path)
st.dataframe(daily_df.head(10), use_container_width=True, hide_index=True)

# --- 3. Individual Stock Stress + Anomaly Markers ---
st.subheader("Stock-Level Stress & Anomaly Markers")
symbols = sorted(stock_df["symbol"].unique())
default_idx = symbols.index("RELIANCE") if "RELIANCE" in symbols else 0
selected_symbol = st.selectbox("Select stock", options=symbols, index=default_idx)

sym_df = stock_df[stock_df["symbol"] == selected_symbol].dropna(subset=["stress_score"])
fig_sym, ax_sym = plt.subplots(figsize=(12, 3.8))
ax_sym.plot(sym_df["trade_date"], sym_df["stress_score"], linewidth=1.2, label=f"{selected_symbol} Stress")
anoms = sym_df[sym_df["is_anomaly"]]
ax_sym.scatter(
    anoms["trade_date"],
    anoms["stress_score"],
    color="red",
    s=20,
    zorder=3,
    label=f"Anomaly ({len(anoms)} days)",
)
ax_sym.set_ylabel("Stress Score")
ax_sym.set_ylim(0, 105)
ax_sym.grid(alpha=0.3)
ax_sym.legend(loc="upper left")
fig_sym.tight_layout()
st.pyplot(fig_sym)

# --- 4. Last 30 Days Sudden Changes (Date-wise) ---
st.subheader("Sudden Changes (Anomalies) — Last 30 Days")
recent_df = get_recent_anomalies(days=30, gold_path=stock_path)
st.dataframe(recent_df, use_container_width=True, hide_index=True)