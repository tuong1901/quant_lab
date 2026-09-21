"""
Backtest Engine Subsystem (`src/backtest/`).

Historical simulation orchestrator iterating Market Data, Strategy evaluation, Signal translation,
ExecutionEngine order submission & fills, and Portfolio state mark-to-market.
"""

from src.backtest.exceptions import (
    BacktestError,
    BacktestExecutionError,
    InvalidSimulationStateError,
)
from src.backtest.state import BacktestState
from src.backtest.engine import BacktestEngine

__all__ = [
    "BacktestError",
    "BacktestExecutionError",
    "InvalidSimulationStateError",
    "BacktestState",
    "BacktestEngine",
]
