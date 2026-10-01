"""
RiskManager Subsystem (`src/environment/risk_manager.py`).
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from src.engine.order import Order, OrderSide
from src.environment.portfolio_state import PortfolioState


class RiskDecisionResult(Enum):
    ALLOW = "ALLOW"
    REJECT = "REJECT"


@dataclass(frozen=True)
class RiskDecision:
    """
    [PURPOSE]: Immutable result container of a RiskManager order validation check.
    """
    result: RiskDecisionResult
    reason: str = ""

    @property
    def is_allowed(self) -> bool:
        return self.result == RiskDecisionResult.ALLOW


class RiskManager:
    """
    [PURPOSE]: Pre-execution Risk Guardrail checker evaluating position limits, notional limits, leverage, and short permissions.
    """
    def __init__(
        self,
        allow_short: bool = True,
        max_position_size: Optional[float] = None,
        max_notional: Optional[float] = None,
        max_leverage: float = 10.0
    ):
        self.allow_short = allow_short
        self.max_position_size = max_position_size
        self.max_notional = max_notional
        self.max_leverage = max_leverage

    def validate_order(
        self,
        order: Order,
        portfolio_state: PortfolioState,
        mark_price: float
    ) -> RiskDecision:
        existing_pos = portfolio_state.positions.get(order.symbol)

        if order.side == OrderSide.SELL and existing_pos is None and not self.allow_short:
            return RiskDecision(RiskDecisionResult.REJECT, "Shorting is disabled by RiskManager policy.")

        order_notional = order.quantity * mark_price

        if self.max_notional is not None and order_notional > self.max_notional:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Order notional ({order_notional:.2f}) exceeds max_notional limit ({self.max_notional:.2f})."
            )

        if self.max_position_size is not None and order.quantity > self.max_position_size:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Order quantity ({order.quantity:.4f}) exceeds max_position_size limit ({self.max_position_size:.4f})."
            )

        required_margin = order_notional / self.max_leverage
        if required_margin > portfolio_state.available_margin:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Required margin ({required_margin:.2f}) exceeds available margin ({portfolio_state.available_margin:.2f})."
            )

        return RiskDecision(RiskDecisionResult.ALLOW, "Order validated successfully.")


def calculate_risk_position_size(
    account_equity: float,
    risk_per_trade_pct: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """
    [PURPOSE]: Compute quantitative position lot size based on percentage risk per trade and stop loss distance.
    """
    stop_dist = abs(entry_price - stop_loss_price)
    if stop_dist <= 0:
        return 0.0
    risk_amount = account_equity * risk_per_trade_pct
    return risk_amount / stop_dist
