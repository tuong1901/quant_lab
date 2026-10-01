"""
Market & Dataset Subsystem (`src/data`).
"""

from src.data.exceptions import (
    MarketDataException,
    InvalidMarketError,
    InvalidDatasetError,
    CatalogError,
    DatasetNotFoundError,
    DuplicateDatasetError,
    DataValidationError,
    IncompatibleDatasetError,
)
from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.dataset import DataRange, StorageReference, Dataset
from src.data.versioning import calculate_content_hash, verify_dataset_hash
from src.data.catalog import DatasetCatalog
from src.data.loader import MarketData, DatasetLoader, load_m15_ohlcv
from src.data.compatibility import validate_compatible_datasets

__all__ = [
    "MarketDataException",
    "InvalidMarketError",
    "InvalidDatasetError",
    "CatalogError",
    "DatasetNotFoundError",
    "DuplicateDatasetError",
    "DataValidationError",
    "IncompatibleDatasetError",
    "Market",
    "Timeframe",
    "DataRange",
    "StorageReference",
    "Dataset",
    "calculate_content_hash",
    "verify_dataset_hash",
    "DatasetCatalog",
    "MarketData",
    "DatasetLoader",
    "load_m15_ohlcv",
    "validate_compatible_datasets",
]
