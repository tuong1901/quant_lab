"""
Core Subsystem Package (`src/core/`).

Exports primitives, entity IDs, clock protocol/implementations, base events, and base exception.
"""

from src.core.exceptions import QuantSystemError
from src.core.types import (
    Symbol,
    Price,
    Quantity,
    validate_utc_timestamp,
    create_utc_timestamp,
)
from src.core.ids import (
    BaseId,
    ExperimentId,
    RunId,
    StrategyId,
    OrderId,
    FillId,
    DatasetId,
    EventId,
)
from src.core.clock import Clock, HistoricalClock, RealtimeClock
from src.core.events import Event

__all__ = [
    "QuantSystemError",
    "Symbol",
    "Price",
    "Quantity",
    "validate_utc_timestamp",
    "create_utc_timestamp",
    "BaseId",
    "ExperimentId",
    "RunId",
    "StrategyId",
    "OrderId",
    "FillId",
    "DatasetId",
    "EventId",
    "Clock",
    "HistoricalClock",
    "RealtimeClock",
    "Event",
]
