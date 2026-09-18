"""
[PURPOSE]: Calculate dynamic or fixed market slippage.
[DEPENDENCIES]: None.
"""

def calculate_slippage(price: float, atr: float, slippage_factor: float = 0.1) -> float:
    """
    [PURPOSE]: Calculate trade slippage based on local ATR volatility.
    [DEPENDENCIES]: None.
    [ARGS]: price — execution price; atr — current ATR; slippage_factor — multiplier.
    [RETURNS]: Slippage cost per share/unit.
    [SIDE EFFECTS]: None.
    """
    return atr * slippage_factor
