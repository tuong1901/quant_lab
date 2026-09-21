"""
[PURPOSE]: Pure mathematical formula functions for calculating Realized and Unrealized PnL.
[DEPENDENCIES]: src.portfolio.position.
"""

from src.portfolio.position import PositionSide

def calculate_unrealized_pnl(
    side: PositionSide,
    entry_price: float,
    mark_price: float,
    quantity: float
) -> float:
    """
    [PURPOSE]: Compute Mark-to-Market unrealized PnL.
    [DEPENDENCIES]: PositionSide.
    [ARGS]:
        side — PositionSide.LONG or PositionSide.SHORT.
        entry_price — Weighted average entry price.
        mark_price — Current mark price.
        quantity — Open position quantity.
    [RETURNS]: Float unrealized PnL.
    [SIDE EFFECTS]: None (pure calculation).
    """
    if side == PositionSide.LONG:
        return (mark_price - entry_price) * quantity
    else:
        return (entry_price - mark_price) * quantity

def calculate_realized_pnl(
    side: PositionSide,
    entry_price: float,
    exit_price: float,
    closed_quantity: float
) -> float:
    """
    [PURPOSE]: Compute gross realized PnL on closed position quantity.
    [DEPENDENCIES]: PositionSide.
    [ARGS]:
        side — PositionSide.LONG or PositionSide.SHORT.
        entry_price — Weighted average entry price of position being closed.
        exit_price — Price at which position is closed.
        closed_quantity — Quantity being closed (> 0).
    [RETURNS]: Float gross realized PnL.
    [SIDE EFFECTS]: None (pure calculation).
    """
    if side == PositionSide.LONG:
        return (exit_price - entry_price) * closed_quantity
    else:
        return (entry_price - exit_price) * closed_quantity
