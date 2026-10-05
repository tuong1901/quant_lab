"""
Execution Exceptions (`src/trading/execution/exceptions.py`).
"""

from src.data.exceptions import QuantSystemError


class ExecutionError(QuantSystemError):
    """Base exception for execution errors."""
    pass


class InvalidOrderError(ExecutionError):
    """Raised when an order has invalid parameters."""
    pass


class FillError(ExecutionError):
    """Raised when an error occurs during order fill simulation."""
    pass
