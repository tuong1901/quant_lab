"""
Immutable Position Dataclass Container (`src/environment/position.py`).
"""

from dataclasses import dataclass
from src.core.types import PositionSide
from src.environment.exceptions import InvalidPositionError


@dataclass(frozen=True)
class Position:
    """
    [PURPOSE]: Immutable dataclass representing open position exposure for a single symbol.
    """
    symbol: str
    side: PositionSide
    quantity: float
    average_entry_price: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidPositionError(f"Position quantity must be strictly positive (> 0), got {self.quantity}.")
        if self.average_entry_price <= 0:
            raise InvalidPositionError(f"Average entry price must be positive, got {self.average_entry_price}.")

    def notional(self, mark_price: float) -> float:
        """[PURPOSE]: Calculate position notional value = quantity * mark_price."""
        if mark_price <= 0:
            raise InvalidPositionError(f"Mark price must be positive, got {mark_price}.")
        return self.quantity * mark_price

    def with_unrealized_pnl(self, unrealized_pnl: float) -> "Position":
        """[PURPOSE]: Create updated Position copy with new unrealized PnL."""
        return Position(
            symbol=self.symbol,
            side=self.side,
            quantity=self.quantity,
            average_entry_price=self.average_entry_price,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized_pnl,
        )
