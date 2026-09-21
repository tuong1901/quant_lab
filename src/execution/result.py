"""
[PURPOSE]: ExecutionResult audit container aggregating order execution outcome.
[DEPENDENCIES]: dataclasses, typing, src.execution.order, src.execution.fill.
"""

from dataclasses import dataclass
from typing import List
from src.execution.order import OrderStatus
from src.execution.fill import Fill

@dataclass(frozen=True)
class ExecutionResult:
    """
    [PURPOSE]: Immutable summary container of an order's execution result.
    [DEPENDENCIES]: OrderStatus, Fill.
    [ARGS]:
        order_id — Parent order ID.
        status — Final order lifecycle status.
        fills — List of Fill objects generated for the order.
        total_filled_quantity — Sum of executed fill quantities.
        average_fill_price — Volume-weighted average fill price.
        total_fee — Sum of commission fees.
        total_slippage — Sum of trade slippages.
    [RETURNS]: ExecutionResult instance.
    """
    order_id: str
    status: OrderStatus
    fills: List[Fill]
    total_filled_quantity: float
    average_fill_price: float
    total_fee: float
    total_slippage: float

    @classmethod
    def from_fills(cls, order_id: str, status: OrderStatus, fills: List[Fill]) -> "ExecutionResult":
        """
        [PURPOSE]: Construct ExecutionResult by aggregating a list of Fills.
        [DEPENDENCIES]: Fill, OrderStatus.
        [ARGS]: order_id — Order ID; status — OrderStatus; fills — List of Fill instances.
        [RETURNS]: Aggregated ExecutionResult instance.
        """
        if not fills:
            return cls(
                order_id=order_id,
                status=status,
                fills=[],
                total_filled_quantity=0.0,
                average_fill_price=0.0,
                total_fee=0.0,
                total_slippage=0.0,
            )

        total_qty = sum(f.quantity for f in fills)
        total_nominal = sum(f.price * f.quantity for f in fills)
        avg_price = total_nominal / total_qty if total_qty > 0 else 0.0
        total_fee = sum(f.fee for f in fills)
        total_slip = sum(f.slippage for f in fills)

        return cls(
            order_id=order_id,
            status=status,
            fills=list(fills),
            total_filled_quantity=total_qty,
            average_fill_price=avg_price,
            total_fee=total_fee,
            total_slippage=total_slip,
        )
