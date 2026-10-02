"""
Pure PnL Calculation Functions (`src/trading/portfolio/pnl.py`).
"""

from src.trading.portfolio.position import PositionSide
from src.trading.portfolio.exceptions import PortfolioException


def calculate_realized_pnl(
    side: PositionSide,
    entry_price: float,
    exit_price: float,
    quantity: float
) -> float:
    """
    [PURPOSE]: Pure mathematical formula for Realized PnL.
    [DEPENDENCIES]: Used by Portfolio.apply_fill.
    [ARGS]: side (PositionSide), entry_price (float), exit_price (float), quantity (float).
    [RETURNS]: float realized profit or loss.
    [SIDE EFFECTS]: Raises PortfolioException on negative quantity or non-positive prices.
    """
    if quantity < 0:
        raise PortfolioException(f"Quantity must be positive, got {quantity}")
    if entry_price <= 0 or exit_price <= 0:
        raise PortfolioException(f"Prices must be positive, got entry={entry_price}, exit={exit_price}")

    if side == PositionSide.LONG:
        return (exit_price - entry_price) * quantity
    else:
        return (entry_price - exit_price) * quantity


def calculate_unrealized_pnl(
    side: PositionSide,
    entry_price: float,
    mark_price: float,
    quantity: float
) -> float:
    """
    [PURPOSE]: Pure mathematical formula for Mark-to-Market Unrealized PnL.
    [DEPENDENCIES]: Used by Portfolio.mark_to_market.
    [ARGS]: side (PositionSide), entry_price (float), mark_price (float), quantity (float).
    [RETURNS]: float mark-to-market unrealized profit or loss.
    [SIDE EFFECTS]: Raises PortfolioException on negative quantity or non-positive prices.
    """
    if quantity < 0:
        raise PortfolioException(f"Quantity must be positive, got {quantity}")
    if entry_price <= 0 or mark_price <= 0:
        raise PortfolioException(f"Prices must be positive, got entry={entry_price}, mark={mark_price}")

    if side == PositionSide.LONG:
        return (mark_price - entry_price) * quantity
    else:
        return (entry_price - mark_price) * quantity
