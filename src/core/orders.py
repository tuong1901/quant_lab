"""
[PURPOSE]: Dataclass representing an active or historical Order.
[DEPENDENCIES]: core.types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.core.types import Side, OrderType

@dataclass
class Order:
    order_id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float
    price: float
    created_at: datetime
    status: str = "PENDING"
