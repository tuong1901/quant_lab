"""
Typed Configuration Models (`src/config/models.py`).

Defines immutable Dataclass value objects representing parsed configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.dataset import StorageReference
from src.config.exceptions import ConfigValidationError


# --- Environment & System Models ---

@dataclass(frozen=True)
class SystemConfig:
    """
    [PURPOSE]: System identity and timezone settings.
    [DEPENDENCIES]: Used by DefaultEnvConfig.
    """
    name: str
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ConfigValidationError("System name must be a non-empty string.")
        if self.timezone.upper() != "UTC":
            raise ConfigValidationError(f"System timezone must be 'UTC', got '{self.timezone}'")


@dataclass(frozen=True)
class ClockConfig:
    """
    [PURPOSE]: Clock operating mode settings.
    [DEPENDENCIES]: Used by DefaultEnvConfig.
    """
    mode: str = "historical"

    def __post_init__(self) -> None:
        if self.mode not in ("historical", "realtime", "simulated"):
            raise ConfigValidationError(f"Invalid clock mode: '{self.mode}'")


@dataclass(frozen=True)
class ReproducibilityConfig:
    """
    [PURPOSE]: Seed and anchor reproducibility settings.
    [DEPENDENCIES]: Used by DefaultEnvConfig.
    """
    seed: int = 42
    freeze_anchor: bool = True


@dataclass(frozen=True)
class BoundaryConfig:
    """
    [PURPOSE]: Boundary policy settings for datasets and experiments.
    [DEPENDENCIES]: Used by DefaultEnvConfig.
    """
    policy: str = "strict"


@dataclass(frozen=True)
class DefaultEnvConfig:
    """
    [PURPOSE]: Consolidated default environment configuration container.
    [DEPENDENCIES]: Combines SystemConfig, ClockConfig, ReproducibilityConfig, BoundaryConfig.
    """
    name: str
    system: SystemConfig
    clock: ClockConfig
    reproducibility: ReproducibilityConfig
    boundary: BoundaryConfig


# --- Dataset Config Model ---

@dataclass(frozen=True)
class DatasetRefConfig:
    """
    [PURPOSE]: Dataset declaration reference config.
    [DEPENDENCIES]: Uses Market, Timeframe, StorageReference.
    """
    name: str
    dataset_id: str
    version: int
    market: Market
    timeframe: Timeframe
    storage_reference: StorageReference

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ConfigValidationError("DatasetRefConfig name must be a non-empty string.")
        if not self.dataset_id or not isinstance(self.dataset_id, str):
            raise ConfigValidationError("DatasetRefConfig dataset_id must be a non-empty string.")
        if not isinstance(self.version, int) or self.version < 1:
            raise ConfigValidationError(f"DatasetRefConfig version must be >= 1, got {self.version}")


# --- Execution Config Models ---

@dataclass(frozen=True)
class FillConfig:
    """
    [PURPOSE]: Fill model configuration parameters.
    """
    model: str = "ltf_replay"
    timing_market_order: str = "next_bar"


@dataclass(frozen=True)
class SlippageConfig:
    """
    [PURPOSE]: Slippage model configuration parameters.
    """
    model: str = "percentage"
    value: float = 0.0002

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ConfigValidationError(f"Slippage value cannot be negative: {self.value}")


@dataclass(frozen=True)
class FeeConfig:
    """
    [PURPOSE]: Fee model maker and taker commission rates.
    """
    maker: float = 0.0001
    taker: float = 0.0002

    def __post_init__(self) -> None:
        if self.maker < 0 or self.taker < 0:
            raise ConfigValidationError("Fee rates cannot be negative.")


@dataclass(frozen=True)
class FundingConfig:
    """
    [PURPOSE]: Perpetual funding model configuration settings.
    """
    enabled: bool = False


@dataclass(frozen=True)
class ExecutionConfig:
    """
    [PURPOSE]: Consolidated execution subsystem configuration preset.
    [DEPENDENCIES]: Combines FillConfig, SlippageConfig, FeeConfig, FundingConfig.
    """
    name: str
    fill: FillConfig
    slippage: SlippageConfig
    fee: FeeConfig
    funding: FundingConfig


# --- Portfolio & Risk Config Models ---

@dataclass(frozen=True)
class AccountConfig:
    """
    [PURPOSE]: Account initial capital and currency settings.
    """
    initial_capital: float = 10000.0
    currency: str = "USDT"

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ConfigValidationError(f"Initial capital must be > 0, got {self.initial_capital}")


@dataclass(frozen=True)
class LeverageConfig:
    """
    [PURPOSE]: Account leverage settings.
    """
    mode: str = "fixed"
    value: float = 1.0

    def __post_init__(self) -> None:
        if self.value < 1.0:
            raise ConfigValidationError(f"Leverage value must be >= 1.0, got {self.value}")


@dataclass(frozen=True)
class PositionConfig:
    """
    [PURPOSE]: Position sizing and short permission limits.
    """
    allow_short: bool = True
    max_position_size: float = 1.0
    max_notional: float = 50000.0


@dataclass(frozen=True)
class RiskConfig:
    """
    [PURPOSE]: Risk manager guardrail limits.
    """
    max_leverage: float = 5.0
    max_exposure: float = 50000.0


@dataclass(frozen=True)
class PortfolioConfig:
    """
    [PURPOSE]: Consolidated portfolio and risk subsystem configuration preset.
    [DEPENDENCIES]: Combines AccountConfig, LeverageConfig, PositionConfig, RiskConfig.
    """
    name: str
    account: AccountConfig
    leverage: LeverageConfig
    position: PositionConfig
    risk: RiskConfig


# --- Experiment Config Model ---

@dataclass(frozen=True)
class ExperimentTimeConfig:
    """
    [PURPOSE]: Experiment time planning configuration parameters.
    """
    mode: str
    start: datetime
    end: datetime
    resolved_anchor: datetime
    window_duration: Optional[str] = None
    step_duration: Optional[str] = None
    warmup_bars: int = 200

    def __post_init__(self) -> None:
        if self.mode not in ("fixed", "rolling", "expanding", "walk_forward"):
            raise ConfigValidationError(f"Invalid experiment time mode: '{self.mode}'")
        if self.start >= self.end:
            raise ConfigValidationError(f"Experiment start ({self.start}) must be earlier than end ({self.end})")
        if self.warmup_bars < 0:
            raise ConfigValidationError(f"Warmup bars cannot be negative: {self.warmup_bars}")


@dataclass(frozen=True)
class ExperimentConfig:
    """
    [PURPOSE]: Root resolved Experiment configuration object holding references to all subsystems.
    [DEPENDENCIES]: Holds DefaultEnvConfig, Strategy & Execution DatasetRefConfig, ExecutionConfig, PortfolioConfig, ExperimentTimeConfig.
    """
    name: str
    environment: DefaultEnvConfig
    strategy_dataset: DatasetRefConfig
    execution_dataset: DatasetRefConfig
    execution: ExecutionConfig
    portfolio: PortfolioConfig
    time: ExperimentTimeConfig
