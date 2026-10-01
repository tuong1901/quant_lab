"""
Environment & Portfolio Subsystem (`src/environment`).
"""

from src.environment.exceptions import (
    EnvironmentError,
    EnvironmentConstructionError,
    MissingDependencyError,
    EnvironmentValidationError,
    PortfolioException,
    InsufficientMarginError,
    InvalidPositionError,
    RiskRejectError,
    DuplicateFillError,
)
from src.environment.registry import Registry
from src.environment.context import ExecutionContext
from src.environment.environment import Environment
from src.environment.factory import EnvironmentFactory
from src.environment.account import Account
from src.environment.position import Position
from src.environment.pnl import calculate_realized_pnl, calculate_unrealized_pnl
from src.environment.margin import SimpleMarginModel, MarginState
from src.environment.risk_manager import (
    RiskDecisionResult,
    RiskDecision,
    RiskManager,
    calculate_risk_position_size,
)
from src.environment.portfolio_state import PortfolioState
from src.environment.portfolio import Portfolio

__all__ = [
    "EnvironmentError",
    "EnvironmentConstructionError",
    "MissingDependencyError",
    "EnvironmentValidationError",
    "PortfolioException",
    "InsufficientMarginError",
    "InvalidPositionError",
    "RiskRejectError",
    "DuplicateFillError",
    "Registry",
    "ExecutionContext",
    "Environment",
    "EnvironmentFactory",
    "Account",
    "Position",
    "calculate_realized_pnl",
    "calculate_unrealized_pnl",
    "SimpleMarginModel",
    "MarginState",
    "RiskDecisionResult",
    "RiskDecision",
    "RiskManager",
    "calculate_risk_position_size",
    "PortfolioState",
    "Portfolio",
]
