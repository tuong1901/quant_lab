"""
Fee Models (`src/trading/execution/fees.py`).
"""

from abc import ABC, abstractmethod
from src.trading.execution.order import OrderType


class FeeModel(ABC):
    """[PURPOSE]: Abstract interface for commission fee calculation."""
    @abstractmethod
    def calculate_fee(self, order_type: OrderType, fill_value: float) -> float:
        pass


class PercentageFeeModel(FeeModel):
    """[PURPOSE]: Percentage fee model with separate Maker and Taker bps rates."""
    def __init__(self, maker_bps: float = 1.0, taker_bps: float = 2.0):
        self.maker_rate = max(0.0, maker_bps) / 10000.0
        self.taker_rate = max(0.0, taker_bps) / 10000.0

    def calculate_fee(self, order_type: OrderType, fill_value: float) -> float:
        rate = self.maker_rate if order_type == OrderType.LIMIT else self.taker_rate
        return max(0.0, fill_value) * rate
