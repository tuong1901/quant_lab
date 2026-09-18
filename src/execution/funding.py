"""
[PURPOSE]: 8-hour Funding Rate fee calculator for crypto perpetuals.
[DEPENDENCIES]: None.
"""

def calculate_funding_fee(position_notional: float, funding_rate: float) -> float:
    """
    [PURPOSE]: Compute funding fee for perp holding.
    [DEPENDENCIES]: None.
    [ARGS]: position_notional — notional position value; funding_rate — 8h rate.
    [RETURNS]: Funding fee cost (positive = debit, negative = credit).
    [SIDE EFFECTS]: None.
    """
    return position_notional * funding_rate
