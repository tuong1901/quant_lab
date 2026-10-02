"""
BacktestState Progress Tracking Container (`src/engine/state.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

from src.engine.execution.fill import Fill
from src.engine.execution.order import Order
from src.environment.accounting.portfolio_state import PortfolioState
from src.strategies.signal import Signal


@dataclass
class BacktestState:
    """
    [PURPOSE]: Mutable container tracking backtest simulation loop execution progress.
    """
    current_timestamp: Optional[datetime] = None
    bars_processed: int = 0
    signals: List[Signal] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)
    portfolio_states: List[PortfolioState] = field(default_factory=list)
