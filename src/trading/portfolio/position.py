"""
Immutable Position Dataclass Container (`src/trading/portfolio/position.py`).
"""

from dataclasses import dataclass
from src.trading.portfolio.exceptions import InvalidPositionError
from src.strategies.context import PositionSide


@dataclass(frozen=True)
class Position:
    """
    [PURPOSE]: Immutable dataclass representing open position exposure for a single symbol.
    [DEPENDENCIES]: Used across portfolio management and risk systems.
    [ARGS]: symbol, side, quantity, average_entry_price, realized_pnl, unrealized_pnl.
    [RETURNS]: Position instance.
    [SIDE EFFECTS]: None.
    """
    symbol: str
    side: PositionSide
    quantity: float
    average_entry_price: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate position non-negative invariants.
        [DEPENDENCIES]: Called on dataclass initialization.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidPositionError if quantity or average_entry_price <= 0.
        """
        if self.quantity <= 0:
            raise InvalidPositionError(f"Position quantity must be strictly positive (> 0), got {self.quantity}.")
        if self.average_entry_price <= 0:
            raise InvalidPositionError(f"Average entry price must be positive, got {self.average_entry_price}.")

    def notional(self, mark_price: float) -> float:
        """
        [PURPOSE]: Calculate position notional value = quantity * mark_price.
        [DEPENDENCIES]: Called by margin and risk models.
        [ARGS]: mark_price (float).
        [RETURNS]: float notional value.
        [SIDE EFFECTS]: Raises InvalidPositionError if mark_price <= 0.
        """
        if mark_price <= 0:
            raise InvalidPositionError(f"Mark price must be positive, got {mark_price}.")
        return self.quantity * mark_price

    def with_unrealized_pnl(self, unrealized_pnl: float) -> "Position":
        """
        [PURPOSE]: Create updated Position copy with new unrealized PnL.
        [DEPENDENCIES]: Called by mark_to_market in Portfolio.
        [ARGS]: unrealized_pnl (float).
        [RETURNS]: New Position copy.
        [SIDE EFFECTS]: None (pure functional copy).
        """
        return Position(
            symbol=self.symbol,
            side=self.side,
            quantity=self.quantity,
            average_entry_price=self.average_entry_price,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized_pnl,
        )
