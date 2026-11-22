"""Build Gold stock-level and Nifty 50 index-level stress tables using Python + DuckDB SQL."""

from pathlib import Path

import duckdb
import pandas as pd

from stress.common import config
from stress.common.logging_setup import get_logger
from stress.transform.features import add_all_features
from stress.transform.scoring import compute_stress_score, load_stress_weights

logger = get_logger(__name__)

VIX_SYMBOL = "INDIA_VIX"


def build_gold_tables(
    silver_dir: Path = config.SILVER_DIR,
    gold_dir: Path = config.GOLD_DIR,
    weights_path: Path = Path("config/stress_weights.yaml"),
    feature_window: int = 20,
    score_window: int | None = None,
    min_periods: int | None = None,
) -> tuple[Path, Path]:
    """Build stock_stress.parquet and nifty50_stress.parquet from Silver Parquet files."""
    weights, cfg_window, cfg_min_periods = load_stress_weights(weights_path)
    win = score_window if score_window is not None else cfg_window
    min_p = min_periods if min_periods is not None else cfg_min_periods

    candles_root = silver_dir / "candles_daily"
    symbol_dirs = sorted(candles_root.glob("symbol=*"))
    if not symbol_dirs:
        raise FileNotFoundError(f"No Silver symbol folders found in {candles_root}")

    stock_frames: list[pd.DataFrame] = []
    vix_df: pd.DataFrame | None = None

    for sym_dir in symbol_dirs:
        parquet_file = sym_dir / "data.parquet"
        if not parquet_file.exists():
            continue

        symbol = sym_dir.name.split("=", 1)[1].upper()
        df = pd.read_parquet(parquet_file).sort_values("trade_date").reset_index(drop=True)

        if symbol == VIX_SYMBOL:
            vix_df = df[["trade_date", "close"]].rename(columns={"close": "india_vix_close"})
            logger.info("Loaded %d rows for %s", len(vix_df), VIX_SYMBOL)
            continue

        featured = add_all_features(df, window=feature_window)
        scored = compute_stress_score(
            featured, weights=weights, window=win, min_periods=min_p
        )
        stock_frames.append(scored)

    if not stock_frames:
        raise ValueError("No equity Silver Parquet files found to build Gold tables.")

    all_stocks = pd.concat(stock_frames, ignore_index=True)

    # Create empty VIX table if INDIA_VIX was not ingested yet
    if vix_df is None:
        logger.warning("INDIA_VIX Silver data not found; india_vix_close will be NULL.")
        vix_df = pd.DataFrame({"trade_date": pd.to_datetime([]), "india_vix_close": []})

    # Use DuckDB SQL to join India VIX by trade_date and aggregate the Nifty 50 Index Stress Score
    con = duckdb.connect()
    con.register("stocks_raw", all_stocks)
    con.register("vix_raw", vix_df)

    stock_gold_df = con.execute(
        """
        SELECT
            s.*,
            v.india_vix_close
        FROM stocks_raw AS s
        LEFT JOIN vix_raw AS v
            ON s.trade_date = v.trade_date
        ORDER BY s.symbol, s.trade_date
        """
    ).df()

    index_gold_df = con.execute(
        """
        SELECT
            s.trade_date,
            ROUND(AVG(s.stress_score), 2) AS index_stress_score,
            ROUND(MAX(s.stress_score), 2) AS max_stock_stress,
            SUM(CASE WHEN s.is_anomaly THEN 1 ELSE 0 END)::INT AS stocks_in_anomaly,
            COUNT(DISTINCT s.symbol)::INT AS stock_count,
            MAX(v.india_vix_close) AS india_vix_close
        FROM stocks_raw AS s
        LEFT JOIN vix_raw AS v
            ON s.trade_date = v.trade_date
        WHERE s.stress_score IS NOT NULL
        GROUP BY s.trade_date
        ORDER BY s.trade_date
        """
    ).df()
    con.close()

    gold_dir.mkdir(parents=True, exist_ok=True)
    stock_gold_path = gold_dir / "stock_stress.parquet"
    index_gold_path = gold_dir / "nifty50_stress.parquet"

    stock_gold_df.to_parquet(stock_gold_path, index=False)
    index_gold_df.to_parquet(index_gold_path, index=False)

    logger.info("Wrote %d rows to %s", len(stock_gold_df), stock_gold_path)
    logger.info("Wrote %d rows to %s", len(index_gold_df), index_gold_path)
    return stock_gold_path, index_gold_path