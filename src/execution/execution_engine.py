"""
[PURPOSE]: Core ExecutionEngine orchestrator managing order lifecycle, fills, slippage, fees, and audit trails.
[DEPENDENCIES]: dataclasses, datetime, typing, src.execution.order, src.execution.fill, src.execution.result, src.execution.fill_model, src.execution.slippage, src.execution.fee, src.execution.exceptions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.execution.order import Order, OrderStatus
from src.execution.fill import Fill
from src.execution.result import ExecutionResult
from src.execution.fill_model import FillModel, OHLCFillModel
from src.execution.slippage import SlippageModel, FixedSlippageModel
from src.execution.fee import FeeModel, PercentageFeeModel
from src.execution.exceptions import InvalidOrderError

@dataclass(frozen=True)
class ExecutionEvent:
    """
    [PURPOSE]: Immutable audit event log entry tracking execution lifecycle milestones.
    """
    event_type: str
    timestamp: datetime
    order_id: str
    details: Dict[str, Any] = field(default_factory=dict)

class ExecutionEngine:
    """
    [PURPOSE]: Orchestrator for processing orders, generating fills, applying slippage/fees, and emitting audit logs.
    [DEPENDENCIES]: FillModel, SlippageModel, FeeModel, Order, Fill, ExecutionResult.
    """
    def __init__(
        self,
        fill_model: Optional[FillModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        fee_model: Optional[FeeModel] = None
    ):
        self.fill_model = fill_model or OHLCFillModel()
        self.slippage_model = slippage_model or FixedSlippageModel()
        self.fee_model = fee_model or PercentageFeeModel()

        self._active_orders: Dict[str, Order] = {}
        self._completed_orders: Dict[str, Order] = {}
        self._events: List[ExecutionEvent] = []
        self._fill_counter: int = 0

    @property
    def active_orders(self) -> Dict[str, Order]:
        return dict(self._active_orders)

    @property
    def completed_orders(self) -> Dict[str, Order]:
        return dict(self._completed_orders)

    def submit_order(self, order: Order) -> Order:
        """
        [PURPOSE]: Validate and accept a new order into the active execution lifecycle.
        [DEPENDENCIES]: Order, OrderStatus, InvalidOrderError.
        [ARGS]: order — Target Order instance to submit.
        [RETURNS]: Updated Order instance with status ACCEPTED.
        """
        if order.order_id in self._active_orders or order.order_id in self._completed_orders:
            raise InvalidOrderError(f"Order ID '{order.order_id}' already exists in engine.")

        # Log ORDER_SUBMITTED
        self._log_event("ORDER_SUBMITTED", order.created_at, order.order_id, {"symbol": order.symbol, "qty": order.quantity})

        # Transition status to ACCEPTED
        accepted_order = order.with_status(OrderStatus.ACCEPTED)
        self._active_orders[order.order_id] = accepted_order
        self._log_event("ORDER_ACCEPTED", order.created_at, order.order_id, {"status": "ACCEPTED"})
        return accepted_order

    def cancel_order(self, order_id: str, timestamp: Optional[datetime] = None) -> Optional[Order]:
        """
        [PURPOSE]: Cancel an active order.
        [DEPENDENCIES]: Order, OrderStatus.
        [ARGS]: order_id — ID of order to cancel; timestamp — Cancellation timestamp.
        [RETURNS]: Cancelled Order instance if active, else None.
        """
        if order_id not in self._active_orders:
            return None

        current_order = self._active_orders.pop(order_id)
        cancelled_order = current_order.with_status(OrderStatus.CANCELLED)
        self._completed_orders[order_id] = cancelled_order

        ts = timestamp or datetime.now(timezone.utc)
        self._log_event("ORDER_CANCELLED", ts, order_id, {"filled_qty": cancelled_order.filled_quantity})
        return cancelled_order

    def process_market_data(
        self,
        market_data: Any,
        timestamp: Optional[datetime] = None,
        market_context: Optional[Dict[str, Any]] = None
    ) -> List[ExecutionResult]:
        """
        [PURPOSE]: Evaluate active orders against market data, compute fills, slippage, fees, and emit ExecutionResults.
        [DEPENDENCIES]: FillModel, SlippageModel, FeeModel, ExecutionResult, Fill.
        [ARGS]:
            market_data — Market bar(s) payload.
            timestamp — Current timestamp.
            market_context — Optional market context (e.g. ATR for volatility slippage).
        [RETURNS]: List of ExecutionResult objects generated in this processing cycle.
        """
        results: List[ExecutionResult] = []
        active_ids = list(self._active_orders.keys())

        for order_id in active_ids:
            order = self._active_orders[order_id]
            candidates = self.fill_model.determine_fills(order, market_data, market_context)
            if not candidates:
                continue

            order_fills: List[Fill] = []
            current_order_state = order

            for cand in candidates:
                self._fill_counter += 1
                fill_id = f"fill_{self._fill_counter:04d}"

                # Calculate slippage
                actual_price = self.slippage_model.apply(current_order_state, cand.price, market_context)
                slippage_amount = abs(actual_price - cand.price)

                # Calculate fee
                fee_amount = self.fee_model.calculate(current_order_state, actual_price, cand.quantity)

                # Create Fill
                fill = Fill(
                    fill_id=fill_id,
                    order_id=order_id,
                    symbol=current_order_state.symbol,
                    side=current_order_state.side,
                    quantity=cand.quantity,
                    price=actual_price,
                    timestamp=cand.timestamp,
                    fee=fee_amount,
                    fee_currency="USDT",
                    slippage=slippage_amount,
                    metadata={"reason": cand.reason, "theoretical_price": cand.price}
                )
                order_fills.append(fill)

                # Update Order state
                new_filled_qty = current_order_state.filled_quantity + cand.quantity
                if new_filled_qty >= current_order_state.quantity:
                    new_status = OrderStatus.FILLED
                else:
                    new_status = OrderStatus.PARTIALLY_FILLED

                current_order_state = current_order_state.with_status(new_status, additional_filled_qty=cand.quantity)

                # Log events
                self._log_event("FILL_CREATED", cand.timestamp, order_id, {"fill_id": fill_id, "price": actual_price, "qty": cand.quantity})
                if new_status == OrderStatus.FILLED:
                    self._log_event("ORDER_FILLED", cand.timestamp, order_id, {"total_filled": new_filled_qty})

            # Update engine registry state
            if current_order_state.status == OrderStatus.FILLED:
                self._active_orders.pop(order_id, None)
                self._completed_orders[order_id] = current_order_state
            else:
                self._active_orders[order_id] = current_order_state

            # Build ExecutionResult
            exec_result = ExecutionResult.from_fills(order_id, current_order_state.status, order_fills)
            results.append(exec_result)

        return results

    def get_audit_events(self) -> List[ExecutionEvent]:
        """
        [PURPOSE]: Return list of logged audit execution events.
        [RETURNS]: List of ExecutionEvent objects.
        """
        return list(self._events)

    def _log_event(self, event_type: str, ts: datetime, order_id: str, details: Dict[str, Any]) -> None:
        """
        [PURPOSE]: Internal helper to append audit log events.
        """
        self._events.append(ExecutionEvent(event_type=event_type, timestamp=ts, order_id=order_id, details=details))
