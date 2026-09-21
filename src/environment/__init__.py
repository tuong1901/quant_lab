"""
Environment Subsystem (`src/environment/`).

The runtime composition layer of the quant research system, responsible for constructing
and exposing a coherent environment world containing Clock, MarketData, Execution,
Portfolio, Config, and Registry dependencies.
"""

from src.environment.exceptions import (
    EnvironmentError,
    EnvironmentConstructionError,
    MissingDependencyError,
    EnvironmentValidationError,
)
from src.environment.registry import Registry
from src.environment.environment import Environment
from src.environment.context import ExecutionContext
from src.environment.factory import EnvironmentFactory

__all__ = [
    "EnvironmentError",
    "EnvironmentConstructionError",
    "MissingDependencyError",
    "EnvironmentValidationError",
    "Registry",
    "Environment",
    "ExecutionContext",
    "EnvironmentFactory",
]
