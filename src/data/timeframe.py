from datetime import datetime, timezone
from typing import Union
from enum import Enum
from src.data.exceptions import DataValidationError

# Shared Primitive Type Aliases
Symbol = str
Price = float
Quantity = float


def validate_utc_timestamp(dt: datetime) -> datetime:
    """
    [PURPOSE]: Validate that a datetime object is timezone-aware and strictly set to UTC.
    [DEPENDENCIES]: Uses DataValidationError.
    [ARGS]: dt — Datetime object to validate.
    [RETURNS]: Validated UTC datetime object.
    [SIDE EFFECTS]: Raises DataValidationError if naive or missing timezone info.
    """
    if not isinstance(dt, datetime):
        raise DataValidationError(f"Expected datetime object, got {type(dt)}")

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise DataValidationError(f"Timestamp must be UTC timezone-aware, got naive datetime: {dt}")

    return dt.astimezone(timezone.utc)


def create_utc_timestamp(val: Union[str, datetime]) -> datetime:
    """
    [PURPOSE]: Convert ISO 8601 string or naive/aware datetime into a canonical UTC-aware datetime.
    [DEPENDENCIES]: Calls validate_utc_timestamp.
    [ARGS]: val — Datetime object or ISO string (e.g. '2026-09-18T15:30:00Z').
    [RETURNS]: Canonical UTC datetime.
    [SIDE EFFECTS]: None.
    """
    try:
        if isinstance(val, datetime):
            dt = val
        elif isinstance(val, str):
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        else:
            raise DataValidationError(f"Cannot parse UTC timestamp from {type(val)}")
    except ValueError as error:
        raise DataValidationError(f"Invalid ISO-8601 timestamp: {val!r}") from error

    return validate_utc_timestamp(dt)


class Timeframe(Enum):
    """
    [PURPOSE]: Enum representing standardized candle bar timeframes.
    """
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    def to_seconds(self) -> int:
        """[RETURNS]: Duration of timeframe bar in seconds."""
        mapping = {
            Timeframe.M1: 60,
            Timeframe.M5: 300,
            Timeframe.M15: 900,
            Timeframe.M30: 1800,
            Timeframe.H1: 3600,
            Timeframe.H4: 14400,
            Timeframe.D1: 86400,
        }
        return mapping[self]

    def to_minutes(self) -> int:
        """[RETURNS]: Duration of timeframe bar in minutes."""
        return self.to_seconds() // 60

    @classmethod
    def from_string(cls, val: str) -> "Timeframe":
        """[RETURNS]: Timeframe enum matching string representation."""
        clean = val.lower().strip()
        for tf in cls:
            if tf.value == clean or tf.name.lower() == clean:
                return tf
        raise DataValidationError(f"Unknown timeframe string: '{val}'")

    @classmethod
    def parse(cls, val: str) -> "Timeframe":
        """[RETURNS]: Alias for from_string."""
        return cls.from_string(val)

