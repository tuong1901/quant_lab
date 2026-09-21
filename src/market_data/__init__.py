"""
Market & Dataset Subsystem (`src/market_data/`).

Exports domain models, catalog, loader, versioning, and exceptions.
"""

from src.market_data.exceptions import (
    MarketDataException,
    InvalidMarketError,
    InvalidDatasetError,
    CatalogError,
    DatasetNotFoundError,
    DuplicateDatasetError,
    DataValidationError,
    IncompatibleDatasetError,
)
from src.market_data.market import Market
from src.market_data.timeframe import Timeframe
from src.market_data.dataset import DataRange, StorageReference, Dataset
from src.market_data.versioning import calculate_content_hash, verify_dataset_hash
from src.market_data.catalog import DatasetCatalog
from src.market_data.loader import MarketData, DatasetLoader
from src.market_data.compatibility import validate_compatible_datasets

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
    "validate_compatible_datasets",
]
