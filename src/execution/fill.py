"""
[PURPOSE]: Immutable Fill dataclass representing an executed trade fill.
[DEPENDENCIES]: dataclasses, datetime, typing, src.execution.order.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
from src.execution.order import OrderSide

@dataclass(frozen=True)
class Fill:
    """
    [PURPOSE]: Immutable record of an executed trade fill.
    [DEPENDENCIES]: OrderSide.
    [ARGS]:
        fill_id — Unique fill identifier.
        order_id — Identifier of parent order.
        symbol — Instrument symbol.
        side — OrderSide (BUY/SELL).
        quantity — Executed fill quantity (> 0).
        price — Executed fill price (> 0).
        timestamp — Timezone-aware execution timestamp.
        fee — Transaction commission fee.
        fee_currency — Currency denomination of fee.
        slippage — Trade slippage amount applied to theoretical price.
        metadata — Additional metadata dictionary.
    [RETURNS]: Fill instance.
    [SIDE EFFECTS]: Raises ValueError if quantity or price <= 0 or missing timezone.
    """
    fill_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    fee: float = 0.0
    fee_currency: str = "USDT"
    slippage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Fill quantity must be positive, got {self.quantity}.")
        if self.price <= 0:
            raise ValueError(f"Fill price must be positive, got {self.price}.")
        if self.timestamp.tzinfo is None:
            raise ValueError("Fill timestamp must be timezone-aware.")
