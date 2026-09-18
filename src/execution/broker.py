"""
[PURPOSE]: Abstract Broker interface and HistoricalBroker implementation.
[DEPENDENCIES]: abc, typing, src.execution.order, src.execution.result.
"""

from abc import ABC, abstractmethod
from typing import List, Any
from src.execution.order import Order
from src.execution.result import ExecutionResult

class Broker(ABC):
    """
    [PURPOSE]: Abstract gateway interface for broker interaction (Historical, Paper, Live).
    """
    @abstractmethod
    def execute_orders(self, orders: List[Order], market_data: Any) -> List[ExecutionResult]:
        """
        [PURPOSE]: Execute a list of orders against market data or live broker.
        [DEPENDENCIES]: Order, ExecutionResult.
        [ARGS]:
            orders — List of active Order instances.
            market_data — Market data payload.
        [RETURNS]: List of ExecutionResult objects.
        """
        pass

class HistoricalBroker(Broker):
    """
    [PURPOSE]: Historical backtest broker wrapper using ExecutionEngine.
    [DEPENDENCIES]: Broker, ExecutionEngine.
    """
    def __init__(self, execution_engine: Any):
        self.engine = execution_engine

    def execute_orders(self, orders: List[Order], market_data: Any) -> List[ExecutionResult]:
        results = []
        for order in orders:
            self.engine.submit_order(order)
        # Process market data
        timestamp = market_data.get('timestamp') if isinstance(market_data, dict) else getattr(market_data, 'timestamp', None)
        return self.engine.process_market_data(market_data, timestamp=timestamp)
