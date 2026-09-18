"""
[PURPOSE]: Define event classes for Event-Driven Quant Architecture.
[DEPENDENCIES]: core.types.
[ARGS]: N/A.
[RETURNS]: N/A.
[SIDE EFFECTS]: None.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

@dataclass
class Event:
    """
    [PURPOSE]: Base Event class for system messaging.
    [DEPENDENCIES]: None.
    """
    timestamp: datetime

@dataclass
class MarketDataEvent(Event):
    """
    [PURPOSE]: Market data update event (Tick or Bar close).
    [DEPENDENCIES]: Event.
    """
    symbol: str
    data: Dict[str, Any]

@dataclass
class SignalEvent(Event):
    """
    [PURPOSE]: Signal event emitted by Strategy engine.
    [DEPENDENCIES]: Event.
    """
    symbol: str
    side: str
    strength: float

@dataclass
class OrderEvent(Event):
    """
    [PURPOSE]: Order event dispatched to Execution Engine.
    [DEPENDENCIES]: Event.
    """
    symbol: str
    order_type: str
    side: str
    quantity: float
    price: float

@dataclass
class FillEvent(Event):
    """
    [PURPOSE]: Execution fill event emitted by Broker/Simulator.
    [DEPENDENCIES]: Event.
    """
    symbol: str
    side: str
    quantity: float
    fill_price: float
    commission: float
    slippage: float
