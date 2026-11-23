"""Apache Airflow DAG: Daily Nifty 50 Market Stress Pipeline (Mon-Fri 16:30 IST)."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="nifty50_market_stress_daily",
    description="Ingest NSE Nifty 50 + India VIX, validate Silver, build SQL Gold, sync to ADLS",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    # 11:00 UTC = 16:30 IST (1 hour after NSE market close), Monday to Friday
    schedule="0 11 * * 1-5",
    catchup=False,
    tags=["nifty50", "medallion", "adls"],
) as dag:
    check_instruments = BashOperator(
        task_id="check_instruments",
        bash_command="uv run python scripts/check_instruments.py",
    )

    run_medallion_pipeline = BashOperator(
        task_id="run_bronze_silver_gold",
        bash_command="uv run python pipelines/run_all.py",
    )

    upload_to_adls = BashOperator(
        task_id="upload_to_azure_data_lake",
        bash_command="uv run python pipelines/run_upload_adls.py",
    )

    check_instruments >> run_medallion_pipeline >> upload_to_adls