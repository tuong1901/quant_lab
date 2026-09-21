"""
Core Event Model (`src/core/events.py`).

Defines base immutable Event structure for event-driven architecture.
"""

from dataclasses import dataclass
from datetime import datetime

from src.core.ids import EventId
from src.core.types import validate_utc_timestamp
from src.core.exceptions import QuantSystemError


@dataclass(frozen=True)
class Event:
    """
    [PURPOSE]: Base immutable Event representation.
    [DEPENDENCIES]: Uses EventId and validate_utc_timestamp.
    [ARGS]:
        event_id — Unique EventId identifier.
        timestamp — UTC timestamp when event occurred.
        sequence — Monotonic sequence integer for deterministic ordering.
    [RETURNS]: Frozen Event instance.
    [SIDE EFFECTS]: Enforces UTC timestamp and sequence >= 0.
    """
    event_id: EventId
    timestamp: datetime
    sequence: int = 0

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate event attributes upon creation.
        """
        if not isinstance(self.event_id, EventId):
            raise QuantSystemError(f"Expected EventId instance, got {type(self.event_id)}")

        validate_utc_timestamp(self.timestamp)

        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise QuantSystemError(f"Sequence must be a non-negative integer, got {self.sequence}")
