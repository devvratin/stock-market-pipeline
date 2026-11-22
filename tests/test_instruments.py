import gzip
import json

from stress.ingest.instruments import (
    build_equity_map,
    find_india_vix_key,
    load_instruments,
    resolve_nifty50,
    symbol_to_key,
)

SAMPLE_INSTRUMENTS = [
    {
        "segment": "NSE_EQ",
        "instrument_type": "EQ",
        "trading_symbol": "RELIANCE",
        "instrument_key": "NSE_EQ|INE002A01018",
    },
    {
        "segment": "NSE_FO",
        "instrument_type": "FUT",
        "trading_symbol": "RELIANCE FUT",
        "instrument_key": "NSE_FO|99999",
    },
    {
        "segment": "NSE_INDEX",
        "instrument_type": "INDEX",
        "name": "India VIX",
        "trading_symbol": "INDIA VIX",
        "instrument_key": "NSE_INDEX|India VIX",
    },
]


def test_load_gzipped_instruments(tmp_path):
    gz_file = tmp_path / "NSE.json.gz"
    with gzip.open(gz_file, "wt", encoding="utf-8") as f:
        json.dump(SAMPLE_INSTRUMENTS, f)

    loaded = load_instruments(gz_file)
    assert len(loaded) == 3


def test_build_equity_map_and_symbol_to_key():
    equity_map = build_equity_map(SAMPLE_INSTRUMENTS)

    assert equity_map == {"RELIANCE": "NSE_EQ|INE002A01018"}
    assert symbol_to_key("reliance", equity_map) == "NSE_EQ|INE002A01018"
    assert symbol_to_key("UNKNOWN", equity_map) is None


def test_find_india_vix_key():
    assert find_india_vix_key(SAMPLE_INSTRUMENTS) == "NSE_INDEX|India VIX"


def test_resolve_nifty50_tracks_missing():
    equity_map = build_equity_map(SAMPLE_INSTRUMENTS)
    resolved, missing = resolve_nifty50(["RELIANCE", "FAKECORP"], equity_map)

    assert resolved == {"RELIANCE": "NSE_EQ|INE002A01018"}
    assert missing == ["FAKECORP"]