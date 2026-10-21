"""Immutable market-data metadata governed by the strict data contract."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Type, TypeVar
import uuid

import yaml

from src.data.exceptions import DataValidationError, InvalidDatasetError
from src.data.market import Market
from src.data.timeframe import Timeframe, create_utc_timestamp
from src.data.columns import ColumnPolicy

T = TypeVar("T", bound="BaseId")

@dataclass(frozen=True)
class BaseId:
    """
    [PURPOSE]: Provide a validated immutable string identifier for domain entities.
    [DEPENDENCIES]: DataValidationError.
    [ARGS]: value — Non-empty identifier string.
    [RETURNS]: Immutable BaseId.
    [SIDE EFFECTS]: Raises DataValidationError for invalid identifiers.
    """

    value: str

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate and trim the identifier value.
        [DEPENDENCIES]: DataValidationError.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises DataValidationError for empty identifiers.
        """
        if not isinstance(self.value, str) or not self.value.strip():
            raise DataValidationError(f"{self.__class__.__name__} value must be a non-empty string.")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        """
        [PURPOSE]: Return the identifier text.
        [DEPENDENCIES]: BaseId.value.
        [ARGS]: None.
        [RETURNS]: Identifier text.
        [SIDE EFFECTS]: None.
        """
        return self.value

    @classmethod
    def generate(cls: Type[T], prefix: str = "") -> T:
        """
        [PURPOSE]: Generate a compact unique typed identifier.
        [DEPENDENCIES]: uuid4.
        [ARGS]: prefix — Optional identifier prefix.
        [RETURNS]: New instance of the concrete BaseId subclass.
        [SIDE EFFECTS]: None.
        """
        unique_value = uuid.uuid4().hex[:12]
        return cls(f"{prefix}_{unique_value}" if prefix else unique_value)


@dataclass(frozen=True)
class DatasetId(BaseId):
    """Typed compatibility identifier for Dataset-related references."""


@dataclass(frozen=True)
class DataRange:
    """
    [PURPOSE]: Define dataset coverage as a UTC half-open interval [start, end).
    [DEPENDENCIES]: create_utc_timestamp.
    [ARGS]: start — Inclusive UTC bound; end — Exclusive UTC bound.
    [RETURNS]: Immutable canonical DataRange.
    [SIDE EFFECTS]: Raises InvalidDatasetError when bounds are invalid.
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Canonicalize bounds to UTC and enforce start < end.
        [DEPENDENCIES]: create_utc_timestamp.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidDatasetError when timestamp or range validation fails.
        """
        try:
            start = create_utc_timestamp(self.start)
            end = create_utc_timestamp(self.end)
        except DataValidationError as error:
            raise InvalidDatasetError(str(error)) from error
        if start >= end:
            raise InvalidDatasetError("DataRange is [start, end) and requires start < end.")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)


@dataclass(frozen=True)
class StorageReference:
    """
    [PURPOSE]: Point to one local CSV or Parquet dataset file.
    [DEPENDENCIES]: InvalidDatasetError.
    [ARGS]: path — File path; format — csv or parquet.
    [RETURNS]: Immutable storage reference.
    [SIDE EFFECTS]: Raises InvalidDatasetError for unsupported storage metadata.
    """

    path: str
    format: str

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Normalize and validate the physical storage descriptor.
        [DEPENDENCIES]: InvalidDatasetError.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidDatasetError for invalid path or format.
        """
        normalized_format = self.format.lower().strip() if isinstance(self.format, str) else ""
        if not isinstance(self.path, str) or not self.path.strip():
            raise InvalidDatasetError("Storage path must be a non-empty string.")
        if normalized_format not in {"csv", "parquet"}:
            raise InvalidDatasetError("Storage format must be csv or parquet.")
        object.__setattr__(self, "path", self.path.strip())
        object.__setattr__(self, "format", normalized_format)


@dataclass(frozen=True)
class Dataset:
    """
    [PURPOSE]: Bind market metadata, physical storage and an expected SHA-256 fingerprint.
    [DEPENDENCIES]: Market, Timeframe, DataRange, StorageReference.
    [ARGS]: dataset_id, market, timeframe, data_range, storage_reference, content_hash, version, columns.
    [RETURNS]: Immutable Dataset descriptor.
    [SIDE EFFECTS]: Raises InvalidDatasetError for malformed metadata.
    """

    dataset_id: str
    market: Market
    timeframe: Timeframe
    data_range: DataRange
    storage_reference: StorageReference
    content_hash: str
    version: str = "v1"
    columns: ColumnPolicy = field(default_factory=ColumnPolicy)

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate stable identity and expected SHA-256 digest.
        [DEPENDENCIES]: InvalidDatasetError.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidDatasetError for malformed descriptor fields.
        """
        if not isinstance(self.columns, ColumnPolicy):
            raise InvalidDatasetError("columns must be a ColumnPolicy.")
        if not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise InvalidDatasetError("dataset_id must be a non-empty string.")
        if not isinstance(self.version, str) or not self.version.strip():
            raise InvalidDatasetError("version must be a non-empty string.")
        if not isinstance(self.content_hash, str) or len(self.content_hash) != 64:
            raise InvalidDatasetError("content_hash must be a 64-character SHA-256 digest.")
        try:
            int(self.content_hash, 16)
        except ValueError as error:
            raise InvalidDatasetError("content_hash must be hexadecimal.") from error
        object.__setattr__(self, "dataset_id", self.dataset_id.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "content_hash", self.content_hash.lower())

    @property
    def identity(self) -> str:
        """
        [PURPOSE]: Return stable dataset identity.
        [DEPENDENCIES]: Dataset metadata.
        [ARGS]: None.
        [RETURNS]: dataset_id:version.
        [SIDE EFFECTS]: None.
        """
        return f"{self.dataset_id}:{self.version}"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Dataset":
        """
        [PURPOSE]: Parse one strict Dataset descriptor YAML document.
        [DEPENDENCIES]: yaml.safe_load, Market, Timeframe, DataRange, StorageReference.
        [ARGS]: yaml_path — Dataset descriptor path.
        [RETURNS]: Dataset descriptor.
        [SIDE EFFECTS]: Reads YAML and raises InvalidDatasetError for malformed content.
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as handle:
                raw: dict[str, Any] = yaml.safe_load(handle) or {}
            return cls(
                dataset_id=raw["dataset_id"],
                version=str(raw.get("version", "v1")),
                market=Market(**raw["market"]),
                timeframe=Timeframe.from_string(raw["timeframe"]),
                data_range=DataRange(**raw["data_range"]),
                storage_reference=StorageReference(**raw["storage_reference"]),
                content_hash=raw["content_hash"],
                columns=ColumnPolicy.from_dict(raw.get("columns")),
            )
        except (KeyError, TypeError, yaml.YAMLError) as error:
            raise InvalidDatasetError(f"Invalid dataset YAML {yaml_path!r}: {error}") from error

    def to_yaml(self, yaml_path: str) -> None:
        """
        [PURPOSE]: Write this Dataset descriptor as portable YAML metadata.
        [DEPENDENCIES]: yaml.safe_dump.
        [ARGS]: yaml_path — Target descriptor path.
        [RETURNS]: None.
        [SIDE EFFECTS]: Writes the descriptor YAML file.
        """
        payload = {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "market": {
                "venue": self.market.venue,
                "symbol": self.market.symbol,
                "quote_currency": self.market.quote_currency,
                "market_type": self.market.market_type,
            },
            "timeframe": self.timeframe.value,
            "data_range": {"start": self.data_range.start.isoformat(), "end": self.data_range.end.isoformat()},
            "storage_reference": {"path": self.storage_reference.path, "format": self.storage_reference.format},
            "content_hash": self.content_hash,
            "columns": self.columns.to_dict(),
        }
        Path(yaml_path).parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False)
