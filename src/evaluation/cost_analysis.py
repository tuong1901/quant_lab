"""
[PURPOSE]: Analyze fee drag and slippage friction impact on strategy performance.
[DEPENDENCIES]: pandas.
"""

import pandas as pd

def compute_fee_drag_ratio(gross_pnl: float, net_pnl: float) -> float:
    """
    [PURPOSE]: Compute Fee Drag Ratio = (Gross PnL - Net PnL) / Gross PnL.
    [DEPENDENCIES]: None.
    [ARGS]: gross_pnl — total PnL before fees; net_pnl — total PnL after fees.
    [RETURNS]: Float ratio.
    [SIDE EFFECTS]: None.
    """
    if gross_pnl == 0:
        return 0.0
    return (gross_pnl - net_pnl) / abs(gross_pnl)
