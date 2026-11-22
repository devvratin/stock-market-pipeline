from datetime import UTC, datetime

from stress.common import config
from stress.common.logging_setup import get_logger
from stress.common.timeutil import IST, is_market_hours, to_ist


def test_utc_converts_to_ist():
    # 04:00 UTC should equal 09:30 IST (+05:30)
    utc_dt = datetime(2026, 11, 20, 4, 0, tzinfo=UTC)
    ist_dt = to_ist(utc_dt)

    assert ist_dt.tzinfo == IST
    assert ist_dt.hour == 9
    assert ist_dt.minute == 30


def test_is_market_hours():
    # Friday 09:30 IST (04:00 UTC) -> open
    assert is_market_hours(datetime(2026, 11, 20, 4, 0, tzinfo=UTC)) is True

    # Friday 16:30 IST (11:00 UTC) -> closed
    assert is_market_hours(datetime(2026, 11, 20, 11, 0, tzinfo=UTC)) is False

    # Saturday 10:30 IST (05:00 UTC) -> weekend, closed
    assert is_market_hours(datetime(2026, 11, 21, 5, 0, tzinfo=UTC)) is False


def test_config_exposes_medallion_paths():
    assert config.BRONZE_DIR == config.DATA_DIR / "bronze"
    assert config.SILVER_DIR == config.DATA_DIR / "silver"
    assert config.GOLD_DIR == config.DATA_DIR / "gold"
    assert isinstance(config.REDIRECT_URI, str)


def test_get_logger_no_duplicate_handlers():
    logger1 = get_logger("stress.test_logger")
    logger2 = get_logger("stress.test_logger")

    assert logger1 is logger2
    assert len(logger1.handlers) == 1