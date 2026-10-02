"""
Portfolio and Accounting Exceptions (`src/trading/portfolio/exceptions.py`).
"""


from src.data.exceptions import QuantSystemError


class PortfolioException(QuantSystemError):
    """
    [PURPOSE]: Base exception for portfolio accounting and position errors.
    [DEPENDENCIES]: Inherits from QuantSystemError.
    [ARGS]: Standard exception args (message, etc.).
    [RETURNS]: PortfolioException instance.
    [SIDE EFFECTS]: None.
    """
    pass


class InsufficientMarginError(PortfolioException):
    """
    [PURPOSE]: Raised when an order or position requires more margin than available.
    [DEPENDENCIES]: Inherits from PortfolioException.
    [ARGS]: Standard exception args.
    [RETURNS]: InsufficientMarginError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidPositionError(PortfolioException):
    """
    [PURPOSE]: Raised when position parameters or state mutations violate invariants.
    [DEPENDENCIES]: Inherits from PortfolioException.
    [ARGS]: Standard exception args.
    [RETURNS]: InvalidPositionError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class RiskRejectError(PortfolioException):
    """
    [PURPOSE]: Raised when an order violates risk manager constraints.
    [DEPENDENCIES]: Inherits from PortfolioException.
    [ARGS]: Standard exception args.
    [RETURNS]: RiskRejectError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class DuplicateFillError(PortfolioException):
    """
    [PURPOSE]: Raised when attempting to apply a fill ID that was already processed.
    [DEPENDENCIES]: Inherits from PortfolioException.
    [ARGS]: Standard exception args.
    [RETURNS]: DuplicateFillError instance.
    [SIDE EFFECTS]: None.
    """
    pass
