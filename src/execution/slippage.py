"""
[PURPOSE]: Slippage models for transforming theoretical fill prices into realistic execution prices.
[DEPENDENCIES]: abc, typing, src.execution.order, src.execution.exceptions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.execution.order import Order, OrderSide
from src.execution.exceptions import SlippageError

class SlippageModel(ABC):
    """
    [PURPOSE]: Abstract base class for trade slippage models.
    """
    @abstractmethod
    def apply(
        self,
        order: Order,
        theoretical_price: float,
        market_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        [PURPOSE]: Calculate actual fill price after applying market slippage.
        [DEPENDENCIES]: Order.
        [ARGS]:
            order — Order being filled.
            theoretical_price — Raw price computed by FillModel (> 0).
            market_context — Optional context dict containing volatility/ATR.
        [RETURNS]: Actual executed fill price float.
        """
        pass

class FixedSlippageModel(SlippageModel):
    """
    [PURPOSE]: Fixed slippage model based on basis points (bps) or price ticks.
    [DEPENDENCIES]: SlippageModel, Order, OrderSide.
    """
    def __init__(self, bps: float = 0.0, ticks: float = 0.0, tick_size: float = 0.01):
        """
        [ARGS]:
            bps — Slippage in basis points (e.g. 5 bps = 0.05%).
            ticks — Slippage in fixed price ticks.
            tick_size — Instrument tick size step.
        """
        self.bps = bps
        self.ticks = ticks
        self.tick_size = tick_size

    def apply(
        self,
        order: Order,
        theoretical_price: float,
        market_context: Optional[Dict[str, Any]] = None
    ) -> float:
        if theoretical_price <= 0:
            raise SlippageError(f"Theoretical price must be positive, got {theoretical_price}.")

        bps_impact = theoretical_price * (self.bps / 10000.0)
        tick_impact = self.ticks * self.tick_size
        total_impact = bps_impact + tick_impact

        if order.side == OrderSide.BUY:
            return theoretical_price + total_impact
        else:
            return max(0.00000001, theoretical_price - total_impact)

class VolatilitySlippageModel(SlippageModel):
    """
    [PURPOSE]: Volatility-based slippage model proportional to ATR.
    [DEPENDENCIES]: SlippageModel, Order, OrderSide.
    """
    def __init__(self, factor: float = 0.1):
        """
        [ARGS]: factor — Multiplier on ATR (e.g. 0.1 for 10% ATR slippage).
        """
        self.factor = factor

    def apply(
        self,
        order: Order,
        theoretical_price: float,
        market_context: Optional[Dict[str, Any]] = None
    ) -> float:
        if theoretical_price <= 0:
            raise SlippageError(f"Theoretical price must be positive, got {theoretical_price}.")

        atr = 0.0
        if market_context and "atr" in market_context:
            atr = float(market_context["atr"])

        impact = atr * self.factor
        if order.side == OrderSide.BUY:
            return theoretical_price + impact
        else:
            return max(0.00000001, theoretical_price - impact)
