"""
Immutable Dataset Dataclass Container (`src/data/dataset.py`).
"""

from dataclasses import dataclass
from datetime import datetime
import yaml

from src.core.types import validate_utc_timestamp, create_utc_timestamp
from src.data.exceptions import InvalidDatasetError
from src.data.market import Market
from src.data.timeframe import Timeframe


@dataclass(frozen=True)
class DataRange:
    """
    [PURPOSE]: Immutable Dataclass representing temporal bounds [start, end] of a dataset.
    """
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.start)
        validate_utc_timestamp(self.end)
        if self.start >= self.end:
            raise InvalidDatasetError(f"DataRange start ({self.start}) must be earlier than end ({self.end})")


@dataclass(frozen=True)
class StorageReference:
    """
    [PURPOSE]: Immutable pointer reference to physical dataset storage file.
    """
    path: str
    format: str = "parquet"

    def __post_init__(self) -> None:
        if not self.path or not isinstance(self.path, str):
            raise InvalidDatasetError("StorageReference path must be non-empty string.")


@dataclass(frozen=True)
class Dataset:
    """
    [PURPOSE]: Immutable Dataset definition entity.
    """
    dataset_id: str
    market: Market
    timeframe: Timeframe
    data_range: DataRange
    storage_reference: StorageReference
    content_hash: str
    version: str = "v1"

    def __post_init__(self) -> None:
        if not self.dataset_id or not isinstance(self.dataset_id, str):
            raise InvalidDatasetError("dataset_id must be non-empty string.")
        if not self.content_hash or not isinstance(self.content_hash, str):
            raise InvalidDatasetError("content_hash must be non-empty string.")

    @property
    def identity(self) -> str:
        """[RETURNS]: Canonical dataset identity string e.g. 'btcusdt_binance_perp_15m:v1'."""
        return f"{self.dataset_id}:{self.version}"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Dataset":
        """[PURPOSE]: Parse Dataset definition from YAML configuration file."""
        with open(yaml_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        market = Market(
            venue=raw["market"]["venue"],
            symbol=raw["market"]["symbol"],
            quote_currency=raw["market"].get("quote_currency", "USDT"),
            market_type=raw["market"].get("market_type", "PERPETUAL"),
        )
        timeframe = Timeframe.from_string(raw["timeframe"])
        data_range = DataRange(
            start=create_utc_timestamp(raw["data_range"]["start"]),
            end=create_utc_timestamp(raw["data_range"]["end"]),
        )
        storage_reference = StorageReference(
            path=raw["storage_reference"]["path"],
            format=raw["storage_reference"].get("format", "parquet"),
        )

        return cls(
            dataset_id=raw["dataset_id"],
            market=market,
            timeframe=timeframe,
            data_range=data_range,
            storage_reference=storage_reference,
            content_hash=raw["content_hash"],
            version=raw.get("version", "v1"),
        )
