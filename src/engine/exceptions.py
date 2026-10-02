"""
Execution & Backtest Engine Exceptions (`src/engine/exceptions.py`).
"""

from src.core.exceptions import QuantSystemError


class EngineError(QuantSystemError):
    """Base exception for Execution and Backtest Engine errors."""
    pass


class ExecutionError(EngineError):
    pass


class InvalidOrderError(ExecutionError):
    pass


class FillError(ExecutionError):
    pass


class BacktestError(EngineError):
    pass


class BacktestExecutionError(BacktestError):
    pass


class InvalidSimulationStateError(BacktestError):
    pass
