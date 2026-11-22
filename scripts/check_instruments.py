"""Verify that all 50 Nifty 50 symbols and India VIX resolve to Upstox keys."""

from stress.ingest.instruments import (
    build_equity_map,
    download_instruments,
    find_india_vix_key,
    load_instruments,
    load_nifty50_symbols,
    resolve_nifty50,
    symbol_to_key,
)


def main() -> None:
    path = download_instruments()
    instruments = load_instruments(path)
    equity_map = build_equity_map(instruments)

    symbols = load_nifty50_symbols()
    resolved, missing = resolve_nifty50(symbols, equity_map)
    vix_key = find_india_vix_key(instruments)

    print(f"Resolved Nifty 50 symbols: {len(resolved)}/{len(symbols)}")
    print(f"RELIANCE  -> {symbol_to_key('RELIANCE', equity_map)}")
    print(f"India VIX -> {vix_key}")
    if missing:
        print(f"Missing symbols ({len(missing)}): {missing}")


if __name__ == "__main__":
    main()