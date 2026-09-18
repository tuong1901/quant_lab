"""
[PURPOSE]: Margin requirement & leverage checker.
[DEPENDENCIES]: None.
"""

def check_margin_requirement(position_notional: float, leverage: float, available_cash: float) -> bool:
    """
    [PURPOSE]: Check if available cash covers initial margin requirement.
    [DEPENDENCIES]: None.
    """
    required_margin = position_notional / leverage
    return available_cash >= required_margin
