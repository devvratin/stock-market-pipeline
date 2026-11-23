"""Offline unit tests for Phase 10 ADLS Gen2 uploader and Airflow DAG syntax."""

import ast
from pathlib import Path

from stress.cloud.adls import sync_medallion_to_adls


class FakeContainerClient:
    def __init__(self) -> None:
        self.uploads: dict[str, bytes] = {}

    def upload_blob(self, name: str, data, overwrite: bool = False) -> None:
        assert overwrite is True, "Uploads must be idempotent (overwrite=True)"
        self.uploads[name] = data.read()


class FakeBlobServiceClient:
    def __init__(self) -> None:
        self.container = FakeContainerClient()

    def get_container_client(self, container_name: str) -> FakeContainerClient:
        self.container_name = container_name
        return self.container


def test_sync_medallion_to_adls_preserves_partition_paths(tmp_path):
    (tmp_path / "bronze" / "candles_daily" / "symbol=RELIANCE").mkdir(parents=True)
    (tmp_path / "bronze" / "candles_daily" / "symbol=RELIANCE" / "2026-11-20.json").write_text(
        "{}", encoding="utf-8"
    )
    (tmp_path / "silver" / "candles_daily" / "symbol=RELIANCE").mkdir(parents=True)
    (tmp_path / "silver" / "candles_daily" / "symbol=RELIANCE" / "data.parquet").write_bytes(
        b"PAR1"
    )
    (tmp_path / "gold").mkdir(parents=True)
    (tmp_path / "gold" / "nifty50_stress.parquet").write_bytes(b"PAR1")

    fake_client = FakeBlobServiceClient()
    counts = sync_medallion_to_adls(
        data_dir=tmp_path,
        container_name="market-stress",
        blob_service_client=fake_client,
    )

    assert counts == {"bronze": 1, "silver": 1, "gold": 1}
    assert "bronze/candles_daily/symbol=RELIANCE/2026-11-20.json" in fake_client.container.uploads
    assert "silver/candles_daily/symbol=RELIANCE/data.parquet" in fake_client.container.uploads
    assert "gold/nifty50_stress.parquet" in fake_client.container.uploads


def test_airflow_dag_file_has_valid_python_syntax():
    dag_path = Path("dags/nifty_stress_dag.py")
    source = dag_path.read_text(encoding="utf-8")
    ast.parse(source)
    assert "nifty50_market_stress_daily" in source
    assert "0 11 * * 1-5" in source