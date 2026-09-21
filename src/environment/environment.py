"""
Environment domain class encapsulating the runtime composition of dependencies.
"""

from dataclasses import dataclass
from typing import Any
from src.environment.registry import Registry
from src.environment.exceptions import MissingDependencyError, EnvironmentConstructionError


@dataclass(frozen=True)
class Environment:
    """
    [PURPOSE]: Immutable runtime environment container grouping system dependencies.
    [DEPENDENCIES]: Clock, DatasetLoader, ExecutionEngine, Portfolio, ExperimentConfig, Registry.
    [ARGS]:
        clock — CoreClock instance managing simulation time.
        market_data — DatasetLoader instance providing data slices.
        execution — ExecutionEngine instance processing orders into fills.
        portfolio — Portfolio instance tracking account & position state.
        config — ExperimentConfig typed configuration container.
        registry — Registry instance for dynamic or optional services.
    [RETURNS]: Environment instance.
    [SIDE EFFECTS]: Validates non-null presence of all required attributes on init.
    """

    clock: Any
    market_data: Any
    execution: Any
    portfolio: Any
    config: Any
    registry: Registry

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate that no required environment field is None.
        [DEPENDENCIES]: Called automatically by dataclass init.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises MissingDependencyError if any field is None.
        """
        fields = {
            "clock": self.clock,
            "market_data": self.market_data,
            "execution": self.execution,
            "portfolio": self.portfolio,
            "config": self.config,
            "registry": self.registry,
        }
        for field_name, field_val in fields.items():
            if field_val is None:
                raise MissingDependencyError(
                    f"Environment field '{field_name}' cannot be None."
                )
