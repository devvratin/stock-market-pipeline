"""Offline unit tests for Phase 4 Bronze ingestion."""

import json
from pathlib import Path

import requests

from stress.ingest.upstox_client import get_daily_candles, save_bronze_candles

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_candles.json"


def test_get_daily_candles_mocked(monkeypatch):
    sample_data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return sample_data

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    result = get_daily_candles(
        instrument_key="NSE_EQ|INE002A01018",
        from_date="2026-11-19",
        to_date="2026-11-20",
        access_token="fake-token",
        sleep_seconds=0,
    )

    assert captured["url"] == (
        "https://api.upstox.com/v3/historical-candle/"
        "NSE_EQ%7CINE002A01018/days/1/2026-11-20/2026-11-19"
    )
    assert captured["headers"]["Authorization"] == "Bearer fake-token"
    assert result == sample_data


def test_get_daily_candles_retries_on_transient_error(monkeypatch):
    sample_data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    attempts = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return sample_data

    def flaky_get(url, headers, timeout):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise requests.ConnectionError("temporary network blip")
        return FakeResponse()

    monkeypatch.setattr(requests, "get", flaky_get)

    result = get_daily_candles(
        instrument_key="NSE_EQ|INE002A01018",
        from_date="2026-11-19",
        to_date="2026-11-20",
        max_retries=2,
        sleep_seconds=0,
    )

    assert attempts["count"] == 2
    assert len(result["data"]["candles"]) == 2


def test_save_bronze_candles_untouched(tmp_path):
    sample_data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    saved_path = save_bronze_candles(
        symbol="reliance",
        payload=sample_data,
        run_date="2026-11-20",
        bronze_dir=tmp_path,
    )

    expected = tmp_path / "candles_daily" / "symbol=RELIANCE" / "2026-11-20.json"
    assert saved_path == expected
    assert json.loads(saved_path.read_text(encoding="utf-8")) == sample_data