"""
[PURPOSE]: Dataclass representing an open position state.
[DEPENDENCIES]: core.types.
"""

from dataclasses import dataclass
from src.core.types import Side

@dataclass
class Position:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
