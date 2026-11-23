"""DuckDB SQL query helpers for daily stress and recent sudden-change reports."""

from pathlib import Path

import duckdb
import pandas as pd

from stress.common import config

DEFAULT_GOLD_STOCK_PATH = config.GOLD_DIR / "stock_stress.parquet"


def get_daily_stress(
    target_date: str | None = None,
    gold_path: Path = DEFAULT_GOLD_STOCK_PATH,
) -> tuple[str, pd.DataFrame]:
    """Return (resolved_date, DataFrame) of all Nifty 50 stocks ranked by stress on a date."""
    if not gold_path.exists():
        raise FileNotFoundError(
            f"Gold table not found at {gold_path}. Run pipelines/run_all.py first."
        )

    con = duckdb.connect()
    parquet_posix = gold_path.as_posix()

    if target_date is None:
        row = con.execute(
            f"SELECT MAX(trade_date)::DATE::VARCHAR FROM read_parquet('{parquet_posix}')"
        ).fetchone()
        resolved_date = row[0]
    else:
        resolved_date = target_date

    df = con.execute(
        f"""
        SELECT
            trade_date::DATE AS trade_date,
            symbol,
            ROUND(close, 2) AS close,
            ROUND(daily_return * 100, 2) AS return_pct,
            ROUND(volume_spike, 2) AS volume_spike,
            stress_score,
            is_anomaly,
            ROUND(india_vix_close, 2) AS india_vix
        FROM read_parquet('{parquet_posix}')
        WHERE trade_date::DATE = CAST(? AS DATE)
        ORDER BY stress_score DESC NULLS LAST, symbol ASC
        """,
        [resolved_date],
    ).df()
    con.close()
    return resolved_date, df


def get_recent_anomalies(
    days: int = 30,
    gold_path: Path = DEFAULT_GOLD_STOCK_PATH,
) -> pd.DataFrame:
    """Return stocks with sudden return or volume changes over the last N days, date-wise."""
    if not gold_path.exists():
        raise FileNotFoundError(
            f"Gold table not found at {gold_path}. Run pipelines/run_all.py first."
        )

    con = duckdb.connect()
    parquet_posix = gold_path.as_posix()

    df = con.execute(
        f"""
        WITH bounds AS (
            SELECT MAX(trade_date)::DATE AS max_date
            FROM read_parquet('{parquet_posix}')
        )
        SELECT
            s.trade_date::DATE AS trade_date,
            s.symbol,
            ROUND(s.close, 2) AS close,
            ROUND(s.daily_return * 100, 2) AS return_pct,
            ROUND(s.volume_spike, 2) AS volume_spike,
            s.stress_score,
            CASE
                WHEN s.is_return_anomaly AND s.is_volume_anomaly THEN 'Return + Volume'
                WHEN s.is_return_anomaly THEN 'Return Shock'
                ELSE 'Volume Spike'
            END AS trigger_reason
        FROM read_parquet('{parquet_posix}') AS s
        CROSS JOIN bounds AS b
        WHERE s.is_anomaly = TRUE
          AND s.trade_date::DATE >= b.max_date - CAST(? AS INTEGER)
        ORDER BY s.trade_date DESC, s.stress_score DESC NULLS LAST
        """,
        [days],
    ).df()
    con.close()
    return df