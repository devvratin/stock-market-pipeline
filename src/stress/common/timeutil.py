"""Timezone and NSE market-hours helpers."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def to_ist(ts: datetime) -> datetime:
    """Convert a datetime to Asia/Kolkata (IST). Assumes UTC if timezone-naive."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(IST)


def is_market_hours(ts: datetime) -> bool:
    """Return True if timestamp falls within NSE trading hours (Mon-Fri, 09:15-15:30 IST)."""
    ist_dt = to_ist(ts)
    if ist_dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    return MARKET_OPEN <= ist_dt.time() <= MARKET_CLOSE