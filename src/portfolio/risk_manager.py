"""
[PURPOSE]: RiskManager subsystem verifying order constraints prior to ExecutionEngine submission.
[DEPENDENCIES]: enum, dataclasses, typing, src.execution.order, src.portfolio.portfolio_state.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from src.execution.order import Order, OrderSide
from src.portfolio.portfolio_state import PortfolioState

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
    [DEPENDENCIES]: Order, PortfolioState, RiskDecision.
    """
    def __init__(
        self,
        allow_short: bool = True,
        max_position_size: Optional[float] = None,
        max_notional: Optional[float] = None,
        max_leverage: float = 10.0
    ):
        """
        [ARGS]:
            allow_short — Boolean flag permitting opening Short positions.
            max_position_size — Maximum allowed quantity per position.
            max_notional — Maximum allowed notional value per position/order.
            max_leverage — Maximum allowed leverage multiplier.
        """
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
        """
        [PURPOSE]: Validate an order against configured risk policies before sending to ExecutionEngine.
        [DEPENDENCIES]: Order, PortfolioState, RiskDecision.
        [ARGS]:
            order — Proposed Order to validate.
            portfolio_state — Current snapshot of PortfolioState.
            mark_price — Current mark price of symbol.
        [RETURNS]: RiskDecision (ALLOW or REJECT with reason).
        """
        existing_pos = portfolio_state.positions.get(order.symbol)

        # 1. Shorting permission check
        if order.side == OrderSide.SELL and existing_pos is None and not self.allow_short:
            return RiskDecision(RiskDecisionResult.REJECT, "Shorting is disabled by RiskManager policy.")

        order_notional = order.quantity * mark_price

        # 2. Max Notional check
        if self.max_notional is not None and order_notional > self.max_notional:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Order notional ({order_notional:.2f}) exceeds max_notional limit ({self.max_notional:.2f})."
            )

        # 3. Max Position Size check
        if self.max_position_size is not None and order.quantity > self.max_position_size:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Order quantity ({order.quantity:.4f}) exceeds max_position_size limit ({self.max_position_size:.4f})."
            )

        # 4. Margin sufficiency check
        required_margin = order_notional / self.max_leverage
        if required_margin > portfolio_state.available_margin:
            return RiskDecision(
                RiskDecisionResult.REJECT,
                f"Required margin ({required_margin:.2f}) exceeds available margin ({portfolio_state.available_margin:.2f})."
            )

        return RiskDecision(RiskDecisionResult.ALLOW, "Order validated successfully.")
