"""
Core Primitive Types & UTC Temporal Helpers (`src/core/types.py`).

Provides temporal UTC validation and shared primitive type aliases.
"""

from datetime import datetime, timezone
from typing import Union

from src.core.exceptions import QuantSystemError

# Shared Primitive Type Aliases
Symbol = str
Price = float
Quantity = float


def validate_utc_timestamp(dt: datetime) -> datetime:
    """
    [PURPOSE]: Validate that a datetime object is timezone-aware and strictly set to UTC.
    [DEPENDENCIES]: Uses QuantSystemError.
    [ARGS]: dt — Datetime object to validate.
    [RETURNS]: Validated UTC datetime object.
    [SIDE EFFECTS]: Raises QuantSystemError if naive or missing timezone info.
    """
    if not isinstance(dt, datetime):
        raise QuantSystemError(f"Expected datetime object, got {type(dt)}")

    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise QuantSystemError(f"Timestamp must be UTC timezone-aware, got naive datetime: {dt}")

    return dt


def create_utc_timestamp(val: Union[str, datetime]) -> datetime:
    """
    [PURPOSE]: Convert ISO 8601 string or naive/aware datetime into a canonical UTC-aware datetime.
    [DEPENDENCIES]: Calls validate_utc_timestamp.
    [ARGS]: val — Datetime object or ISO string (e.g. '2026-09-18T15:30:00Z').
    [RETURNS]: Canonical UTC datetime.
    [SIDE EFFECTS]: None.
    """
    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, str):
        val_clean = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(val_clean)
    else:
        raise QuantSystemError(f"Cannot parse UTC timestamp from {type(val)}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return validate_utc_timestamp(dt)
