"""
StrategyContext read-only container (`src/strategies/context.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from enum import Enum
from src.data.timeframe import validate_utc_timestamp
from src.strategies.exceptions import StrategyContextError


class PositionSide(Enum):
    """
    [PURPOSE]: Enum representing market exposure directional side (LONG / SHORT).
    """
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class StrategyContext:
    """
    [PURPOSE]: Narrow read-only context passed into Strategy.on_bar() evaluation.
    [DEPENDENCIES]: PositionSide, validate_utc_timestamp, StrategyContextError.
    [ARGS]:
        timestamp — UTC timestamp of current bar.
        price — Latest close or market price (> 0).
        position_side — Optional active position side (LONG, SHORT, or None for FLAT).
        features — Read-only key-value dictionary of calculated indicator/feature values.
    [RETURNS]: Frozen StrategyContext instance.
    [SIDE EFFECTS]: Validates timestamp and positive price bounds on init.
    """

    timestamp: datetime
    price: float
    position_side: Optional[PositionSide] = None
    features: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate context attributes on construction.
        [DEPENDENCIES]: Called by dataclass init.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises StrategyContextError if price <= 0 or timestamp invalid.
        """
        if self.price <= 0:
            raise StrategyContextError(f"StrategyContext price must be > 0, got {self.price}")

        try:
            validate_utc_timestamp(self.timestamp)
        except Exception as e:
            raise StrategyContextError(f"StrategyContext timestamp error: {e}") from e
