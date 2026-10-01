"""
ExecutionEngine Orchestrator (`src/engine/execution_engine.py`).
"""

from datetime import datetime
from typing import Dict, List, Optional

from src.core.types import validate_utc_timestamp
from src.engine.fee import FeeModel, PercentageFeeModel
from src.engine.fill_model import FillModel, OHLCFillModel
from src.engine.order import Order, OrderStatus
from src.engine.result import ExecutionResult
from src.engine.slippage import SlippageModel, FixedSlippageModel


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

        base_price = market_data.get("open", market_data.get("close", 0.0))

        for order_id, order in list(self.pending_orders.items()):
            exec_price = self.slippage_model.calculate_execution_price(order, base_price)
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
