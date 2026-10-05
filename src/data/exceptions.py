"""
Market Data Exceptions (`src/data/exceptions.py`).
"""

class QuantSystemError(Exception):
    """Base exception for all quantitative trading system errors."""
    pass


class MarketDataException(QuantSystemError):
    """Base exception for market data errors."""
    pass


class InvalidMarketError(MarketDataException):
    pass


class InvalidDatasetError(MarketDataException):
    pass


class CatalogError(MarketDataException):
    pass


class DatasetNotFoundError(CatalogError):
    pass


class DuplicateDatasetError(CatalogError):
    pass


class DataValidationError(MarketDataException):
    pass


class IncompatibleDatasetError(MarketDataException):
    pass
