"""
[PURPOSE]: System-wide custom exception definitions.
[DEPENDENCIES]: None.
"""

class QuantSystemException(Exception):
    """Base exception for quant lab framework."""
    pass

class LookaheadBiasError(QuantSystemException):
    """Raised when causal data access rules are violated."""
    pass

class InsufficientMarginError(QuantSystemException):
    """Raised when account margin is insufficient to execute order."""
    pass
