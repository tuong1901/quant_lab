"""
Broker Gateway Interface & Historical Implementation (`src/engine/broker.py`).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from src.engine.order import Order, OrderStatus
from src.engine.result import ExecutionResult


class Broker(ABC):
    """[PURPOSE]: Gateway interface for Order submission and execution handling."""
    @abstractmethod
    def submit_order(self, order: Order) -> Order:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass


class HistoricalBroker(Broker):
    """[PURPOSE]: Historical simulation broker holding order book state during backtesting."""
    def __init__(self) -> None:
        self.orders: Dict[str, Order] = {}

    def submit_order(self, order: Order) -> Order:
        accepted = order.with_status(OrderStatus.ACCEPTED)
        self.orders[accepted.order_id] = accepted
        return accepted

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.orders[order_id] = self.orders[order_id].with_status(OrderStatus.CANCELLED)
            return True
        return False
