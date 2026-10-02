"""
Order Data Models (`src/trading/execution/order.py`).
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.data.timeframe import validate_utc_timestamp
from src.data.dataset import BaseId
from src.trading.execution.exceptions import InvalidOrderError, ExecutionError


@dataclass(frozen=True)
class OrderId(BaseId):
    pass


@dataclass(frozen=True)
class FillId(BaseId):
    pass


@dataclass(frozen=True)
class EventId(BaseId):
    pass


@dataclass(frozen=True)
class Event:
    event_id: EventId
    timestamp: datetime
    sequence: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, EventId):
            raise ExecutionError(f"Expected EventId instance, got {type(self.event_id)}")
        validate_utc_timestamp(self.timestamp)
        if not isinstance(self.sequence, int) or self.sequence < 0:
            raise ExecutionError(f"Sequence must be a non-negative integer, got {self.sequence}")


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
