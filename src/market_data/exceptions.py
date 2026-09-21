"""
Custom exceptions for the Market & Dataset Subsystem (`src/market_data/`).
"""


class MarketDataException(Exception):
    """
    [PURPOSE]: Base exception class for all market_data subsystem errors.
    [DEPENDENCIES]: Inherits from Python's base Exception.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidMarketError(MarketDataException):
    """
    [PURPOSE]: Raised when a Market identity or attribute validation fails (venue, symbol, market_type, currency).
    [DEPENDENCIES]: Inherits from MarketDataException.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidDatasetError(MarketDataException):
    """
    [PURPOSE]: Raised when a Dataset metadata or structural validation fails.
    [DEPENDENCIES]: Inherits from MarketDataException.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class CatalogError(MarketDataException):
    """
    [PURPOSE]: Base exception for dataset catalog operations.
    [DEPENDENCIES]: Inherits from CatalogError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class DatasetNotFoundError(CatalogError):
    """
    [PURPOSE]: Raised when a requested dataset_id and version pair is not found in the catalog.
    [DEPENDENCIES]: Inherits from CatalogError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class DuplicateDatasetError(CatalogError):
    """
    [PURPOSE]: Raised when registering a dataset that already exists in the catalog.
    [DEPENDENCIES]: Inherits from CatalogError.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class DataValidationError(MarketDataException):
    """
    [PURPOSE]: Raised when OHLCV market data content fails validation (OHLC bounds, timestamps, hash mismatch).
    [DEPENDENCIES]: Inherits from MarketDataException.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass


class IncompatibleDatasetError(MarketDataException):
    """
    [PURPOSE]: Raised when strategy dataset and execution dataset are incompatible.
    [DEPENDENCIES]: Inherits from MarketDataException.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: None.
    """
    pass
