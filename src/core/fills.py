"""
[PURPOSE]: Dataclass representing an executed trade fill.
[DEPENDENCIES]: core.types.
"""

from dataclasses import dataclass
from datetime import datetime
from src.core.types import Side

@dataclass
class Fill:
    fill_id: str
    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    commission: float
    slippage: float
    timestamp: datetime
