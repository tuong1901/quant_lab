"""
[PURPOSE]: Define Order enums and immutable Order dataclass for Execution subsystem.
[DEPENDENCIES]: enum, dataclasses, datetime, typing, src.execution.exceptions.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from src.execution.exceptions import InvalidOrderError

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass(frozen=True)
class Order:
    """
    [PURPOSE]: Immutable Order dataclass representing a trade request intent.
    [DEPENDENCIES]: OrderSide, OrderType, OrderStatus, InvalidOrderError.
    [ARGS]:
        order_id — Unique identifier string.
        symbol — Instrument symbol (e.g. 'BTCUSDT').
        side — OrderSide (BUY/SELL).
        order_type — OrderType (MARKET, LIMIT, STOP, STOP_LIMIT).
        quantity — Order size quantity (must be > 0).
        created_at — Timezone-aware timestamp of order creation.
        status — Current OrderStatus lifecycle state.
        limit_price — Price threshold for Limit orders.
        stop_price — Price threshold for Stop orders.
        filled_quantity — Total quantity filled so far.
        reduce_only — Flag indicating position reduction only.
        metadata — Arbitrary metadata dictionary.
    [RETURNS]: Order instance.
    [SIDE EFFECTS]: Raises InvalidOrderError on validation failure.
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    created_at: datetime
    status: OrderStatus = OrderStatus.CREATED
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: float = 0.0
    reduce_only: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidOrderError(f"Order quantity must be positive, got {self.quantity}.")
        if self.created_at.tzinfo is None:
            raise InvalidOrderError("Order created_at timestamp must be timezone-aware.")
        if self.order_type == OrderType.LIMIT and (self.limit_price is None or self.limit_price <= 0):
            raise InvalidOrderError(f"LIMIT order requires a positive limit_price, got {self.limit_price}.")
        if self.order_type in {OrderType.STOP, OrderType.STOP_LIMIT} and (self.stop_price is None or self.stop_price <= 0):
            raise InvalidOrderError(f"STOP order requires a positive stop_price, got {self.stop_price}.")

    @property
    def remaining_quantity(self) -> float:
        """
        [PURPOSE]: Compute remaining unfilled quantity.
        [RETURNS]: Float quantity.
        """
        return max(0.0, self.quantity - self.filled_quantity)

    @property
    def is_active(self) -> bool:
        """
        [PURPOSE]: Check if order is in an active lifecycle state.
        [RETURNS]: Boolean.
        """
        return self.status in {OrderStatus.SUBMITTED, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}

    @property
    def is_complete(self) -> bool:
        """
        [PURPOSE]: Check if order has reached a terminal lifecycle state.
        [RETURNS]: Boolean.
        """
        return self.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}

    def with_status(self, new_status: OrderStatus, additional_filled_qty: float = 0.0) -> "Order":
        """
        [PURPOSE]: Create a new copy of Order with updated status and filled_quantity.
        [DEPENDENCIES]: Order.
        [ARGS]: new_status — New OrderStatus; additional_filled_qty — Added filled quantity.
        [RETURNS]: New updated Order instance.
        """
        new_filled = min(self.quantity, self.filled_quantity + additional_filled_qty)
        return Order(
            order_id=self.order_id,
            symbol=self.symbol,
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity,
            created_at=self.created_at,
            status=new_status,
            limit_price=self.limit_price,
            stop_price=self.stop_price,
            filled_quantity=new_filled,
            reduce_only=self.reduce_only,
            metadata=self.metadata.copy(),
        )
