"""
Broker Gateway Interface & Execution Engine (`src/trading/execution/broker.py`).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.data.timeframe import validate_utc_timestamp
from src.trading.execution.order import Order, OrderStatus, OrderType
from src.trading.execution.fill import Fill
from src.trading.execution.fill_model import FillModel, OHLCFillModel
from src.trading.execution.slippage import SlippageModel, FixedSlippageModel
from src.trading.execution.fees import FeeModel, PercentageFeeModel


@dataclass
class ExecutionResult:
    """
    [PURPOSE]: Container collecting fills, updated order state, and audit execution metrics.
    """
    order: Order
    fills: List[Fill] = field(default_factory=list)
    total_fee: float = 0.0
    average_fill_price: float = 0.0

    def calculate_totals(self) -> None:
        if not self.fills:
            self.total_fee = 0.0
            self.average_fill_price = 0.0
            return

        total_val = sum(f.value for f in self.fills)
        total_qty = sum(f.quantity for f in self.fills)
        self.total_fee = sum(f.fee for f in self.fills)
        self.average_fill_price = total_val / total_qty if total_qty > 0 else 0.0


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


class ExecutionEngine:
    """
    [PURPOSE]: Orchestrator managing Order submissions and executing Fills against market data.
    """

    def __init__(
        self,
        fill_model: Optional[FillModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        fee_model: Optional[FeeModel] = None,
    ):
        self.fill_model = fill_model if fill_model is not None else OHLCFillModel()
        self.slippage_model = slippage_model if slippage_model is not None else FixedSlippageModel(slippage_bps=0.0)
        self.fee_model = fee_model if fee_model is not None else PercentageFeeModel(maker_bps=2.0, taker_bps=4.0)
        self.pending_orders: Dict[str, Order] = {}

    def submit_order(self, order: Order) -> Order:
        """[PURPOSE]: Submit Order for pending execution."""
        accepted = order.with_status(OrderStatus.ACCEPTED)
        self.pending_orders[accepted.order_id] = accepted
        return accepted

    def process_market_data(self, market_data: Dict[str, float], timestamp: datetime) -> List[ExecutionResult]:
        """[PURPOSE]: Evaluate pending orders against new market data bar."""
        validate_utc_timestamp(timestamp)
        results: List[ExecutionResult] = []
        filled_order_ids = []

        for order_id, order in list(self.pending_orders.items()):
            reference_price = self.fill_model.determine_reference_price(order, market_data)
            if reference_price is None:
                continue

            # A limit order promises the submitted limit price in this engine.
            # Only market orders pay modeled adverse slippage around their reference price.
            exec_price = reference_price
            if order.order_type == OrderType.MARKET:
                exec_price = self.slippage_model.calculate_execution_price(order, reference_price)
            fee = self.fee_model.calculate_fee(order.order_type, order.quantity * exec_price)

            fill = self.fill_model.simulate_fill(
                order=order,
                market_data=market_data,
                timestamp=timestamp,
                slippage_price=exec_price,
                fee_amount=fee,
            )

            if fill is not None:
                filled_order = order.with_status(OrderStatus.FILLED)
                exec_result = ExecutionResult(
                    order=filled_order,
                    fills=[fill],
                )
                exec_result.calculate_totals()
                results.append(exec_result)
                filled_order_ids.append(order_id)

        for oid in filled_order_ids:
            del self.pending_orders[oid]

        return results
