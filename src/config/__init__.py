"""
Config Layer Package (`src/config/`).

Exports typed config models, config loader, validation engine, and exceptions.
"""

from src.config.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    ConfigReferenceError,
    ConfigCompatibilityError,
)
from src.config.models import (
    SystemConfig,
    ClockConfig,
    ReproducibilityConfig,
    BoundaryConfig,
    DefaultEnvConfig,
    DatasetRefConfig,
    FillConfig,
    SlippageConfig,
    FeeConfig,
    FundingConfig,
    ExecutionConfig,
    AccountConfig,
    LeverageConfig,
    PositionConfig,
    RiskConfig,
    PortfolioConfig,
    ExperimentTimeConfig,
    ExperimentConfig,
)
from src.config.validation import validate_experiment_config
from src.config.loader import ConfigLoader

__all__ = [
    "ConfigError",
    "ConfigFileNotFoundError",
    "ConfigParseError",
    "ConfigValidationError",
    "ConfigReferenceError",
    "ConfigCompatibilityError",
    "SystemConfig",
    "ClockConfig",
    "ReproducibilityConfig",
    "BoundaryConfig",
    "DefaultEnvConfig",
    "DatasetRefConfig",
    "FillConfig",
    "SlippageConfig",
    "FeeConfig",
    "FundingConfig",
    "ExecutionConfig",
    "AccountConfig",
    "LeverageConfig",
    "PositionConfig",
    "RiskConfig",
    "PortfolioConfig",
    "ExperimentTimeConfig",
    "ExperimentConfig",
    "validate_experiment_config",
    "ConfigLoader",
]
