"""
Slippage Models (`src/trading/execution/slippage.py`).
"""

from abc import ABC, abstractmethod
from src.trading.execution.order import Order, OrderSide


class SlippageModel(ABC):
    """[PURPOSE]: Abstract interface for price slippage calculation."""
    @abstractmethod
    def calculate_execution_price(self, order: Order, base_price: float, atr_value: float = 0.0) -> float:
        pass


class FixedSlippageModel(SlippageModel):
    """[PURPOSE]: Fixed bps slippage calculation."""
    def __init__(self, slippage_bps: float = 0.0):
        if slippage_bps < 0:
            raise ValueError("slippage_bps must be non-negative")
        self.slippage_bps = slippage_bps

    def calculate_execution_price(self, order: Order, base_price: float, atr_value: float = 0.0) -> float:
        slip_pct = self.slippage_bps / 10000.0
        if order.side == OrderSide.BUY:
            return base_price * (1.0 + slip_pct)
        else:
            return base_price * (1.0 - slip_pct)


class VolatilitySlippageModel(SlippageModel):
    """[PURPOSE]: Volatility-based slippage calculation using ATR multiplier."""
    def __init__(self, atr_factor: float = 0.05):
        if atr_factor < 0:
            raise ValueError("atr_factor must be non-negative")
        self.atr_factor = atr_factor

    def calculate_execution_price(self, order: Order, base_price: float, atr_value: float = 0.0) -> float:
        slippage_dist = self.atr_factor * max(0.0, atr_value)
        if order.side == OrderSide.BUY:
            return base_price + slippage_dist
        else:
            return base_price - slippage_dist
