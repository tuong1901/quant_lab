"""
Core Entity ID System (`src/core/ids.py`).

Provides distinct, immutable ID wrappers preventing cross-type assignment errors.
"""

from dataclasses import dataclass
import uuid
from typing import Type, TypeVar

from src.core.exceptions import QuantSystemError

T = TypeVar("T", bound="BaseId")


@dataclass(frozen=True)
class BaseId:
    """
    [PURPOSE]: Base immutable value object for entity identification.
    [DEPENDENCIES]: Inherits from dataclass(frozen=True).
    [ARGS]: value — String identifier.
    [RETURNS]: Frozen ID instance.
    [SIDE EFFECTS]: Enforces non-empty string.
    """
    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str) or not self.value.strip():
            raise QuantSystemError(f"{self.__class__.__name__} value must be a non-empty string.")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls: Type[T], prefix: str = "") -> T:
        """
        [PURPOSE]: Auto-generate a unique ID instance using UUID v4 hex.
        [DEPENDENCIES]: Uses stdlib uuid.uuid4().
        [ARGS]: prefix — Optional string prefix.
        [RETURNS]: New ID instance of type cls.
        [SIDE EFFECTS]: None.
        """
        unique_hex = uuid.uuid4().hex[:12]
        full_val = f"{prefix}_{unique_hex}" if prefix else unique_hex
        return cls(value=full_val)


@dataclass(frozen=True)
class ExperimentId(BaseId):
    """[PURPOSE]: Unique identifier for an Experiment."""
    pass


@dataclass(frozen=True)
class RunId(BaseId):
    """[PURPOSE]: Unique identifier for an ExperimentRun."""
    pass


@dataclass(frozen=True)
class StrategyId(BaseId):
    """[PURPOSE]: Unique identifier for a Strategy."""
    pass


@dataclass(frozen=True)
class OrderId(BaseId):
    """[PURPOSE]: Unique identifier for an Order."""
    pass


@dataclass(frozen=True)
class FillId(BaseId):
    """[PURPOSE]: Unique identifier for a Fill."""
    pass


@dataclass(frozen=True)
class DatasetId(BaseId):
    """[PURPOSE]: Unique identifier for a Dataset."""
    pass


@dataclass(frozen=True)
class EventId(BaseId):
    """[PURPOSE]: Unique identifier for an Event."""
    pass
