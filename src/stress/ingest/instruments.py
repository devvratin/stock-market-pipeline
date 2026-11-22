"""Download and resolve Upstox NSE instrument keys."""

import gzip
import json
from pathlib import Path

import requests
import yaml

from stress.common import config
from stress.common.logging_setup import get_logger

logger = get_logger(__name__)

NSE_INSTRUMENTS_URL = (
    "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
)
DEFAULT_INSTRUMENTS_PATH = config.BRONZE_DIR / "instruments" / "NSE.json.gz"
DEFAULT_NIFTY50_YAML = Path("config/nifty50.yaml")


def download_instruments(
    dest_path: Path = DEFAULT_INSTRUMENTS_PATH,
    force: bool = False,
) -> Path:
    """Download Upstox's public NSE instrument master (.json.gz) into Bronze."""
    if dest_path.exists() and not force:
        logger.info("Using cached instrument file: %s", dest_path)
        return dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading NSE instruments from %s", NSE_INSTRUMENTS_URL)
    response = requests.get(NSE_INSTRUMENTS_URL, timeout=60)
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    logger.info("Saved instrument master to %s", dest_path)
    return dest_path


def load_instruments(path: Path = DEFAULT_INSTRUMENTS_PATH) -> list[dict]:
    """Read and parse the gzipped JSON instrument master file."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def build_equity_map(instruments: list[dict]) -> dict[str, str]:
    """Filter instruments to NSE equities (segment=NSE_EQ, type=EQ)."""
    return {
        item["trading_symbol"].upper(): item["instrument_key"]
        for item in instruments
        if item.get("segment") == "NSE_EQ"
        and item.get("instrument_type") == "EQ"
        and item.get("trading_symbol")
        and item.get("instrument_key")
    }


def symbol_to_key(symbol: str, equity_map: dict[str, str]) -> str | None:
    """Resolve an NSE trading symbol (e.g. RELIANCE) to its Upstox instrument_key."""
    key = equity_map.get(symbol.strip().upper())
    if key is None:
        logger.warning("Instrument key not found for symbol: %s", symbol)
    return key


def find_india_vix_key(instruments: list[dict]) -> str | None:
    """Look up the NSE index instrument_key for India VIX."""
    for item in instruments:
        if (
            item.get("segment") == "NSE_INDEX"
            and item.get("instrument_type") == "INDEX"
        ):
            name = (item.get("name") or "").upper()
            symbol = (item.get("trading_symbol") or "").upper()
            if name == "INDIA VIX" or symbol == "INDIA VIX":
                return item["instrument_key"]
    logger.warning("India VIX instrument key not found.")
    return None


def load_nifty50_symbols(yaml_path: Path = DEFAULT_NIFTY50_YAML) -> list[str]:
    """Load the list of Nifty 50 symbols from YAML."""
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    return [s.strip().upper() for s in data["symbols"]]


def resolve_nifty50(
    symbols: list[str],
    equity_map: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    """Resolve all symbols to instrument keys and return (resolved, missing)."""
    resolved: dict[str, str] = {}
    missing: list[str] = []

    for sym in symbols:
        key = symbol_to_key(sym, equity_map)
        if key:
            resolved[sym] = key
        else:
            missing.append(sym)

    logger.info(
        "Resolved %d/%d symbols (%d missing).",
        len(resolved),
        len(symbols),
        len(missing),
    )
    return resolved, missing