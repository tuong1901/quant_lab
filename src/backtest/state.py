"""
BacktestState audit trail container (`src/backtest/state.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from src.strategies.signal import Signal
from src.execution.order import Order
from src.execution.fill import Fill
from src.portfolio.portfolio_state import PortfolioState


@dataclass
class BacktestState:
    """
    [PURPOSE]: Container object capturing simulation state and audit logs during backtest execution.
    [DEPENDENCIES]: Signal, Order, Fill, PortfolioState.
    [ARGS]:
        current_timestamp — Active simulation timestamp.
        bars_processed — Counter of total market bars processed.
        signals — Chronological list of generated Signal objects.
        orders — Chronological list of generated Order objects.
        fills — Chronological list of generated Fill objects.
        portfolio_states — Chronological list of PortfolioState snapshots.
    [RETURNS]: BacktestState instance.
    [SIDE EFFECTS]: Mutable container populated during simulation run.
    """

    current_timestamp: Optional[datetime] = None
    bars_processed: int = 0
    signals: List[Signal] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)
    portfolio_states: List[PortfolioState] = field(default_factory=list)
