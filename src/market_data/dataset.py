"""
Dataset Domain Model (`src/market_data/dataset.py`).

Represents an immutable historical market dataset snapshot.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union

from src.market_data.exceptions import InvalidDatasetError
from src.market_data.market import Market
from src.market_data.timeframe import Timeframe


@dataclass(frozen=True)
class DataRange:
    """
    [PURPOSE]: Value object specifying the exact time boundary of a dataset.
    [DEPENDENCIES]: Used by Dataset; enforces UTC aware datetimes.
    [ARGS]:
        start — Start datetime (must be UTC aware).
        end — End datetime (must be UTC aware).
    [RETURNS]: Frozen DataRange instance.
    [SIDE EFFECTS]: None.
    """
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate timezone awareness and start < end constraint.
        [DEPENDENCIES]: Called automatically by dataclass __init__.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: None.
        """
        if not isinstance(self.start, datetime) or not isinstance(self.end, datetime):
            raise InvalidDatasetError("DataRange start and end must be datetime objects.")

        if self.start.tzinfo is None or self.start.tzinfo.utcoffset(self.start) is None:
            raise InvalidDatasetError(f"DataRange start datetime must be UTC timezone aware, got naive: {self.start}")

        if self.end.tzinfo is None or self.end.tzinfo.utcoffset(self.end) is None:
            raise InvalidDatasetError(f"DataRange end datetime must be UTC timezone aware, got naive: {self.end}")

        if self.start >= self.end:
            raise InvalidDatasetError(f"DataRange start ({self.start}) must be strictly earlier than end ({self.end}).")

    def to_dict(self) -> Dict[str, str]:
        """
        [PURPOSE]: Convert DataRange to dictionary representation with ISO 8601 strings.
        [DEPENDENCIES]: Used by dataset serialization.
        [ARGS]: None.
        [RETURNS]: Dict containing ISO format start and end strings.
        [SIDE EFFECTS]: None.
        """
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataRange":
        """
        [PURPOSE]: Parse DataRange from a dictionary containing ISO strings.
        [DEPENDENCIES]: Uses datetime.fromisoformat and timezone.utc.
        [ARGS]: data — Dict with 'start' and 'end' keys.
        [RETURNS]: DataRange instance.
        [SIDE EFFECTS]: None.
        """
        if not isinstance(data, dict) or "start" not in data or "end" not in data:
            raise InvalidDatasetError("DataRange dictionary must contain 'start' and 'end'.")

        def _parse_utc_datetime(val: Any) -> datetime:
            if isinstance(val, datetime):
                dt = val
            elif isinstance(val, str):
                val_str = val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(val_str)
            else:
                raise InvalidDatasetError(f"Cannot parse datetime from {val}")

            if dt.tzinfo is None:
                # Assign UTC if naive ISO string was provided
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        start_dt = _parse_utc_datetime(data["start"])
        end_dt = _parse_utc_datetime(data["end"])
        return cls(start=start_dt, end=end_dt)


@dataclass(frozen=True)
class StorageReference:
    """
    [PURPOSE]: Value object pointing to physical storage reference location.
    [DEPENDENCIES]: Used by Dataset.
    [ARGS]:
        type — Storage protocol/type (e.g. 'local', 's3', 'parquet').
        path — File system path or uri.
    [RETURNS]: Frozen StorageReference instance.
    [SIDE EFFECTS]: None.
    """
    type: str
    path: str

    def __post_init__(self) -> None:
        if not self.type or not isinstance(self.type, str):
            raise InvalidDatasetError("StorageReference type must be a non-empty string.")
        if not self.path or not isinstance(self.path, str):
            raise InvalidDatasetError("StorageReference path must be a non-empty string.")

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.type,
            "path": self.path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageReference":
        if not isinstance(data, dict) or "type" not in data or "path" not in data:
            raise InvalidDatasetError("StorageReference dictionary must contain 'type' and 'path'.")
        return cls(type=str(data["type"]), path=str(data["path"]))


@dataclass(frozen=True)
class Dataset:
    """
    [PURPOSE]: Immutable Domain Model representing a historical market dataset identity & metadata.
    [DEPENDENCIES]: Uses Market, Timeframe, DataRange, StorageReference.
    [ARGS]:
        dataset_id — Unique string identifier for the dataset (e.g. 'btcusdt_binance_perp_15m').
        market — Market instance describing venue/symbol/type/currency.
        timeframe — Timeframe enum instance.
        version — Integer version number (e.g. 3).
        data_range — DataRange instance specifying start/end UTC datetimes.
        source — Dictionary specifying data provider source (e.g. {'provider': 'binance'}).
        content_hash — Deterministic content fingerprint string.
        schema_version — Schema format version (default 1).
        storage_reference — StorageReference instance pointing to storage location.
        metadata — Optional arbitrary metadata dict.
    [RETURNS]: Frozen Dataset instance.
    [SIDE EFFECTS]: Enforces immutability.
    """
    dataset_id: str
    market: Market
    timeframe: Timeframe
    version: int
    data_range: DataRange
    source: Dict[str, Any]
    content_hash: str
    storage_reference: StorageReference
    schema_version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate all dataset fields upon creation.
        [DEPENDENCIES]: Called automatically by dataclass __init__.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Normalizes dataset_id and parses timeframe.
        """
        if not self.dataset_id or not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise InvalidDatasetError("Dataset dataset_id must be a non-empty string.")

        if not isinstance(self.market, Market):
            raise InvalidDatasetError(f"Dataset market must be a Market instance, got {type(self.market)}")

        tf = Timeframe.parse(self.timeframe)
        object.__setattr__(self, "timeframe", tf)

        if not isinstance(self.version, int) or self.version < 1:
            raise InvalidDatasetError(f"Dataset version must be an integer >= 1, got {self.version}")

        if not isinstance(self.data_range, DataRange):
            raise InvalidDatasetError(f"Dataset data_range must be a DataRange instance, got {type(self.data_range)}")

        if not isinstance(self.source, dict):
            raise InvalidDatasetError("Dataset source must be a dictionary.")

        if not self.content_hash or not isinstance(self.content_hash, str) or not self.content_hash.strip():
            raise InvalidDatasetError("Dataset content_hash must be a non-empty string.")

        if not isinstance(self.storage_reference, StorageReference):
            raise InvalidDatasetError(
                f"Dataset storage_reference must be a StorageReference instance, got {type(self.storage_reference)}"
            )

        object.__setattr__(self, "dataset_id", self.dataset_id.strip())

    @property
    def identity(self) -> str:
        """
        [PURPOSE]: Return unique dataset identity string in format 'dataset_id:v{version}'.
        [DEPENDENCIES]: Combines dataset_id and version.
        [ARGS]: None.
        [RETURNS]: str e.g. 'btcusdt_binance_perp_15m:v3'.
        [SIDE EFFECTS]: None.
        """
        return f"{self.dataset_id}:v{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        """
        [PURPOSE]: Convert Dataset to dictionary representation for YAML catalog storage or serialization.
        [DEPENDENCIES]: Calls sub-component to_dict methods.
        [ARGS]: None.
        [RETURNS]: Dictionary of dataset configuration.
        [SIDE EFFECTS]: None.
        """
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "market": self.market.to_dict(),
            "timeframe": str(self.timeframe),
            "data_range": self.data_range.to_dict(),
            "source": self.source,
            "content_hash": self.content_hash,
            "schema_version": self.schema_version,
            "storage_reference": self.storage_reference.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dataset":
        """
        [PURPOSE]: Deserialize dictionary representation into a Dataset object.
        [DEPENDENCIES]: Parses sub-component dicts for Market, DataRange, StorageReference.
        [ARGS]: data — Dictionary containing dataset properties.
        [RETURNS]: Dataset object.
        [SIDE EFFECTS]: None.
        """
        if not isinstance(data, dict):
            raise InvalidDatasetError("Dataset data must be a dictionary.")

        required_keys = {
            "dataset_id",
            "market",
            "timeframe",
            "version",
            "data_range",
            "source",
            "content_hash",
            "storage_reference",
        }
        missing = required_keys - set(data.keys())
        if missing:
            raise InvalidDatasetError(f"Missing required dataset fields: {missing}")

        market = Market.from_dict(data["market"])
        timeframe = Timeframe.parse(data["timeframe"])
        data_range = DataRange.from_dict(data["data_range"])
        storage_ref = StorageReference.from_dict(data["storage_reference"])

        return cls(
            dataset_id=str(data["dataset_id"]),
            market=market,
            timeframe=timeframe,
            version=int(data["version"]),
            data_range=data_range,
            source=dict(data["source"]),
            content_hash=str(data["content_hash"]),
            schema_version=int(data.get("schema_version", 1)),
            storage_reference=storage_ref,
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Dataset":
        """
        [PURPOSE]: Load and parse a Dataset object directly from a YAML configuration file.
        [DEPENDENCIES]: Uses PyYAML and Dataset.from_dict.
        [ARGS]: yaml_path — Path to the .yaml or .yml configuration file.
        [RETURNS]: Dataset object.
        [SIDE EFFECTS]: Reads file from disk.
        """
        import yaml

        if not os.path.exists(yaml_path):
            raise InvalidDatasetError(f"Dataset YAML configuration file not found: '{yaml_path}'")

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise InvalidDatasetError(f"Failed to parse YAML file '{yaml_path}': {str(e)}")

        return cls.from_dict(data)

    def to_yaml(self, yaml_path: str) -> None:
        """
        [PURPOSE]: Save Dataset configuration object into a clean YAML configuration file.
        [DEPENDENCIES]: Uses PyYAML and Dataset.to_dict.
        [ARGS]: yaml_path — Destination path for .yaml file.
        [RETURNS]: None.
        [SIDE EFFECTS]: Writes file to disk.
        """
        import yaml

        parent_dir = os.path.dirname(yaml_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.to_dict(), f, sort_keys=False, allow_unicode=True)

