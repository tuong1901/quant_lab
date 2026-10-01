"""
BacktestResult Immutable Audit Snapshot Container (`src/engine/backtest_result.py`).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from src.core.types import validate_utc_timestamp
from src.engine.fill import Fill
from src.engine.order import Order
from src.environment.portfolio_state import PortfolioState
from src.strategies.signal import Signal


@dataclass(frozen=True)
class BacktestResult:
    """
    [PURPOSE]: Immutable snapshot containing complete execution history of a backtest run.
    """
    run_id: str
    strategy_id: str
    dataset_id: str
    initial_capital: float
    bars_processed: int
    final_timestamp: datetime
    signals: Tuple[Signal, ...]
    orders: Tuple[Order, ...]
    fills: Tuple[Fill, ...]
    portfolio_history: Tuple[PortfolioState, ...]
    final_portfolio: PortfolioState

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.final_timestamp)
