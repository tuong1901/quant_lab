"""
ExecutionResult Audit Trail Container (`src/engine/result.py`).
"""

from dataclasses import dataclass, field
from typing import List
from src.engine.execution.fill import Fill
from src.engine.execution.order import Order


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
