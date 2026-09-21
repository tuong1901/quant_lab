"""
Exceptions for the Backtest Engine Subsystem (`src/backtest/exceptions.py`).
"""

from src.core.exceptions import QuantSystemError


class BacktestError(QuantSystemError):
    """
    [PURPOSE]: Root base exception for all Backtest Engine errors.
    [DEPENDENCIES]: Inherits from src.core.exceptions.QuantSystemError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class BacktestExecutionError(BacktestError):
    """
    [PURPOSE]: Raised when an unrecoverable failure occurs during backtest simulation loop execution.
    [DEPENDENCIES]: Inherits from BacktestError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidSimulationStateError(BacktestError):
    """
    [PURPOSE]: Raised when an invalid simulation state or parameter mismatch occurs during backtest.
    [DEPENDENCIES]: Inherits from BacktestError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass
