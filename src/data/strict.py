"""Compatibility imports for the sole strict data-contract implementation."""

from src.data.loader import DatasetLoader, MarketData, load_m15_ohlcv
from src.data.versioning import CANONICAL_COLUMNS, calculate_content_hash, canonicalize_ohlcv

__all__ = [
    "CANONICAL_COLUMNS",
    "DatasetLoader",
    "MarketData",
    "calculate_content_hash",
    "canonicalize_ohlcv",
    "load_m15_ohlcv",
]
