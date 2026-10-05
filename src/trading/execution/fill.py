"""
Immutable Fill Dataclass (`src/trading/execution/fill.py`).
"""

from dataclasses import dataclass
from datetime import datetime

from src.data.timeframe import validate_utc_timestamp
from src.trading.execution.exceptions import FillError
from src.trading.execution.order import OrderSide


@dataclass(frozen=True)
class Fill:
    """
    [PURPOSE]: Immutable dataclass representing an executed order fill.
    """
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    fee: float
    timestamp: datetime

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.timestamp)
        if self.quantity <= 0:
            raise FillError(f"Fill quantity must be strictly positive (> 0), got {self.quantity}.")
        if self.price <= 0:
            raise FillError(f"Fill price must be strictly positive (> 0), got {self.price}.")
        if self.fee < 0:
            raise FillError(f"Fill fee cannot be negative, got {self.fee}.")

    @property
    def value(self) -> float:
        return self.quantity * self.price
