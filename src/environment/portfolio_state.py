"""
PortfolioState Immutable Snapshot Container (`src/environment/portfolio_state.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

from src.core.types import validate_utc_timestamp
from src.environment.position import Position
from src.environment.exceptions import PortfolioException


@dataclass(frozen=True)
class PortfolioState:
    """
    [PURPOSE]: Immutable point-in-time snapshot of complete portfolio state.
    """
    timestamp: datetime
    balance: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    fees_paid: float
    funding_paid: float
    used_margin: float
    available_margin: float
    positions: Dict[str, Position] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.timestamp)
        if self.balance < 0:
            raise PortfolioException(f"Balance cannot be negative, got {self.balance}")
