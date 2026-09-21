"""
[PURPOSE]: Custom exceptions for the Execution Subsystem.
[DEPENDENCIES]: None.
"""

class ExecutionException(Exception):
    """Base exception for all execution subsystem errors."""
    pass

class InvalidOrderError(ExecutionException):
    """Raised when an order fails validation (e.g. invalid price/quantity)."""
    pass

class FillModelError(ExecutionException):
    """Raised when fill determination fails."""
    pass

class SlippageError(ExecutionException):
    """Raised when slippage calculation fails."""
    pass

class FeeError(ExecutionException):
    """Raised when fee calculation fails."""
    pass
