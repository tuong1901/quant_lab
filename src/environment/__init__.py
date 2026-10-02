"""
Environment package master SSOT exports (`src/environment/__init__.py`).
"""

from src.environment.exceptions import (
    EnvironmentError,
    EnvironmentConstructionError,
    MissingDependencyError,
    EnvironmentValidationError,
    PortfolioException,
    InsufficientMarginError,
    InvalidPositionError,
    DuplicateFillError,
    RiskRejectError,
)
from src.environment.accounting import (
    Account,
    Position,
    calculate_realized_pnl,
    calculate_unrealized_pnl,
    MarginState,
    SimpleMarginModel,
    RiskManager,
    PortfolioState,
    Portfolio,
)
from src.environment.runtime import (
    ExecutionContext,
    Environment,
    EnvironmentFactory,
    Registry,
)

__all__ = [
    "EnvironmentError",
    "EnvironmentConstructionError",
    "MissingDependencyError",
    "EnvironmentValidationError",
    "PortfolioException",
    "InsufficientMarginError",
    "InvalidPositionError",
    "DuplicateFillError",
    "RiskRejectError",
    "Account",
    "Position",
    "calculate_realized_pnl",
    "calculate_unrealized_pnl",
    "MarginState",
    "SimpleMarginModel",
    "RiskManager",
    "PortfolioState",
    "Portfolio",
    "ExecutionContext",
    "Environment",
    "EnvironmentFactory",
    "Registry",
]
