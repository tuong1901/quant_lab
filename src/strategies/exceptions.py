"""
Exceptions for the Strategy Subsystem (`src/strategies/exceptions.py`).
"""

from src.core.exceptions import QuantSystemError


class StrategyError(QuantSystemError):
    """
    [PURPOSE]: Root base exception for all strategy subsystem errors.
    [DEPENDENCIES]: Inherits from src.core.exceptions.QuantSystemError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidSignalError(StrategyError):
    """
    [PURPOSE]: Raised when a Strategy generates an invalid signal payload or unknown signal action.
    [DEPENDENCIES]: Inherits from StrategyError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass


class StrategyContextError(StrategyError):
    """
    [PURPOSE]: Raised when invalid or missing data context is passed to a Strategy.
    [DEPENDENCIES]: Inherits from StrategyError.
    [ARGS]: Standard exception args.
    [RETURNS]: Exception instance.
    [SIDE EFFECTS]: None.
    """
    pass
