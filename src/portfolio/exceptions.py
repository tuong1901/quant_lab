"""
[PURPOSE]: Custom exceptions for the Portfolio & Accounting Subsystem.
[DEPENDENCIES]: None.
"""

class PortfolioException(Exception):
    """Base exception for all portfolio subsystem errors."""
    pass

class InsufficientMarginError(PortfolioException):
    """Raised when available margin is insufficient for position allocation."""
    pass

class InvalidPositionError(PortfolioException):
    """Raised when position state invariants are violated."""
    pass

class RiskRejectError(PortfolioException):
    """Raised when an order fails RiskManager guardrail checks."""
    pass
