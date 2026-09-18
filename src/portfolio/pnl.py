"""
[PURPOSE]: Realized & Unrealized PnL calculator.
[DEPENDENCIES]: None.
"""

def calculate_unrealized_pnl(side: str, entry_price: float, current_price: float, quantity: float) -> float:
    """
    [PURPOSE]: Calculate mark-to-market unrealized PnL.
    [DEPENDENCIES]: None.
    [ARGS]: side — 'BUY' or 'SELL'; entry_price — entry; current_price — mark; quantity — size.
    [RETURNS]: Float unrealized PnL.
    [SIDE EFFECTS]: None.
    """
    if side == "BUY":
        return (current_price - entry_price) * quantity
    else:
        return (entry_price - current_price) * quantity
