"""Immutable completed-trade evidence produced by the portfolio lifecycle."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.data.timeframe import validate_utc_timestamp
from src.trading.portfolio.exceptions import PortfolioException
from src.trading.portfolio.position import PositionSide


@dataclass(frozen=True)
class ClosedTrade:
    """
    [PURPOSE]: Preserve one realized quantity from an opened position through its closing fill.
    [DEPENDENCIES]: Created by Portfolio when a Fill reduces, closes, or reverses a position; consumed by evaluation metrics.
    [ARGS]: Immutable entry/exit evidence, realized gross PnL, and allocated trading costs for one closed quantity.
    [RETURNS]: ClosedTrade instance.
    [SIDE EFFECTS]: Raises PortfolioException when timestamps, quantity, or prices violate trade evidence invariants.
    """

    trade_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_timestamp: datetime
    exit_timestamp: datetime
    entry_price: float
    exit_price: float
    gross_pnl: float
    entry_fee: float
    exit_fee: float
    funding_fee: float = 0.0
    holding_bars: Optional[int] = None
    mae: Optional[float] = None
    mfe: Optional[float] = None
    r_multiple: Optional[float] = None

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate that a closed-trade record is complete and internally consistent.
        [DEPENDENCIES]: Calls validate_utc_timestamp.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises PortfolioException for invalid immutable trade evidence.
        """
        validate_utc_timestamp(self.entry_timestamp)
        validate_utc_timestamp(self.exit_timestamp)
        if self.exit_timestamp < self.entry_timestamp:
            raise PortfolioException("Trade exit timestamp cannot precede entry timestamp.")
        if self.quantity <= 0:
            raise PortfolioException(f"Closed trade quantity must be positive, got {self.quantity}.")
        if self.entry_price <= 0 or self.exit_price <= 0:
            raise PortfolioException("Closed trade entry and exit prices must be positive.")
        if self.entry_fee < 0 or self.exit_fee < 0 or self.funding_fee < 0:
            raise PortfolioException("Closed trade costs cannot be negative.")
        if self.holding_bars is not None and self.holding_bars < 0:
            raise PortfolioException("Closed trade holding_bars cannot be negative.")

    @property
    def total_cost(self) -> float:
        """
        [PURPOSE]: Return all allocated costs that reduce this closed trade's economic PnL.
        [DEPENDENCIES]: Used by net_pnl and downstream evaluation.
        [ARGS]: None.
        [RETURNS]: Sum of entry fee, exit fee, and funding fee.
        [SIDE EFFECTS]: None.
        """
        return self.entry_fee + self.exit_fee + self.funding_fee

    @property
    def net_pnl(self) -> float:
        """
        [PURPOSE]: Return realized gross PnL after only the costs allocated to this trade.
        [DEPENDENCIES]: Used by trade-level evaluation metrics.
        [ARGS]: None.
        [RETURNS]: Economic PnL for this closed trade.
        [SIDE EFFECTS]: None.
        """
        return self.gross_pnl - self.total_cost


@dataclass
class _OpenTradeCycle:
    """Mutable internal accumulator for the still-open quantity of one position cycle."""

    symbol: str
    side: PositionSide
    quantity: float
    entry_timestamp: datetime
    average_entry_price: float
    unallocated_entry_fee: float

