"""
Signal value object and SignalAction enum (`src/strategies/signal.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union

from src.core.ids import StrategyId
from src.core.types import validate_utc_timestamp
from src.strategies.exceptions import InvalidSignalError


class SignalAction(Enum):
    """
    [PURPOSE]: Enum representing target directional strategy intent.
    [DEPENDENCIES]: Used by Signal and Strategy evaluation methods.
    """
    HOLD = "HOLD"
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class Signal:
    """
    [PURPOSE]: Immutable value object representing a strategy's directional signal.
    [DEPENDENCIES]: Uses SignalAction, StrategyId, validate_utc_timestamp, InvalidSignalError.
    [ARGS]:
        timestamp — UTC datetime of the bar/signal.
        action — SignalAction (HOLD, LONG, SHORT).
        strategy_id — Optional StrategyId or string strategy identifier.
        metadata — Optional key-value dictionary for auxiliary signal metadata.
    [RETURNS]: Frozen Signal instance.
    [SIDE EFFECTS]: Validates non-null action and UTC timestamp on init.
    """

    timestamp: datetime
    action: SignalAction
    strategy_id: Optional[Union[StrategyId, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate signal fields and timestamp timezone.
        [DEPENDENCIES]: Called by dataclass initialization.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidSignalError if timestamp or action is invalid.
        """
        if not isinstance(self.action, SignalAction):
            raise InvalidSignalError(f"Invalid signal action: {self.action}")

        try:
            validate_utc_timestamp(self.timestamp)
        except Exception as e:
            raise InvalidSignalError(f"Signal timestamp error: {e}") from e
