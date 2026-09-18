"""
[PURPOSE]: Position Sizing (% Risk per trade) & Guardrail checks.
[DEPENDENCIES]: None.
"""

class RiskManager:
    """
    [PURPOSE]: Calculate trade position size based on % risk model.
    [DEPENDENCIES]: None.
    """
    def calculate_position_size(self, equity: float, risk_pct: float, entry_price: float, stop_loss_price: float) -> float:
        """
        [PURPOSE]: Risk-based position sizing formula: (Equity * Risk%) / abs(Entry - Stop).
        [DEPENDENCIES]: None.
        [ARGS]: equity — current equity; risk_pct — % risk per trade (e.g. 0.01 for 1%); entry_price — entry; stop_loss_price — stop loss.
        [RETURNS]: Calculated quantity float.
        [SIDE EFFECTS]: None.
        """
        risk_amount = equity * risk_pct
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            return 0.0
        return risk_amount / price_risk
