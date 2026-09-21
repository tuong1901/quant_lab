"""
Execution context encapsulating active execution metadata and runtime clock.
"""

from dataclasses import dataclass

from typing import Any
from src.environment.exceptions import EnvironmentConstructionError


@dataclass(frozen=True)
class ExecutionContext:
    """
    [PURPOSE]: Represents lightweight contextual metadata during strategy backtest execution.
    [DEPENDENCIES]: Clock, RunId, DatasetId, ExecutionId.
    [ARGS]:
        clock — Active simulation clock instance.
        run — Unique RunId string identifier.
        dataset_id — Target DatasetId identifier.
        execution_id — Active ExecutionId identifier.
    [RETURNS]: ExecutionContext instance.
    [SIDE EFFECTS]: Validates non-null values on init.
    """

    clock: Any
    run: Any
    dataset_id: Any
    execution_id: Any

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Enforce non-null fields in ExecutionContext.
        [DEPENDENCIES]: Called by dataclass initialization.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises EnvironmentConstructionError if any parameter is None.
        """
        fields = {
            "clock": self.clock,
            "run": self.run,
            "dataset_id": self.dataset_id,
            "execution_id": self.execution_id,
        }
        for name, val in fields.items():
            if val is None:
                raise EnvironmentConstructionError(
                    f"ExecutionContext field '{name}' cannot be None."
                )
