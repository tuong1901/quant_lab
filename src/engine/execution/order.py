"""
Order Data Models (`src/engine/order.py`).
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.core.types import validate_utc_timestamp
from src.engine.exceptions import InvalidOrderError


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Order:
    """
    [PURPOSE]: Immutable Order dataclass representation.
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    created_at: datetime
    price: float = 0.0
    status: OrderStatus = OrderStatus.CREATED

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.created_at)
        if self.quantity <= 0:
            raise InvalidOrderError(f"Order quantity must be strictly positive (> 0), got {self.quantity}.")
        if self.order_type == OrderType.LIMIT and self.price <= 0:
            raise InvalidOrderError(f"LIMIT order requires price > 0, got {self.price}.")

    def with_status(self, new_status: OrderStatus) -> "Order":
        return Order(
            order_id=self.order_id,
            symbol=self.symbol,
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity,
            price=self.price,
            created_at=self.created_at,
            status=new_status,
        )
