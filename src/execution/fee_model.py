"""
[PURPOSE]: Calculate commission fees (Maker/Taker bps).
[DEPENDENCIES]: None.
"""

def calculate_commission(nominal_value: float, fee_bps: float = 4.0) -> float:
    """
    [PURPOSE]: Calculate trade commission cost.
    [DEPENDENCIES]: None.
    [ARGS]: nominal_value — trade notional value; fee_bps — fee in basis points.
    [RETURNS]: Commission amount.
    [SIDE EFFECTS]: None.
    """
    return nominal_value * (fee_bps / 10000.0)
