"""
[PURPOSE]: Unit tests for Market Data subsystem (loader, bounds validation, hash verification).
[DEPENDENCIES]: unittest, pandas, datetime, src.data.
"""

import unittest
import pandas as pd
from datetime import datetime, timezone

from src.data.loader import DatasetLoader
from src.data.exceptions import DataValidationError


class TestUnitMarketData(unittest.TestCase):
    """
    [PURPOSE]: Unit tests for market data loading and validation routines.
    """

    def setUp(self):
        self.loader = DatasetLoader()
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_ohlc_bounds_high_less_than_low_rejected(self):
        """[Market Data Unit]: High < Low MUST be rejected with DataValidationError."""
        df = pd.DataFrame([{
            "timestamp": self.now,
            "open": 100.0,
            "high": 90.0,  # Invalid: high < low
            "low": 95.0,
            "close": 98.0,
            "volume": 10.0,
        }])
        with self.assertRaises(DataValidationError):
            self.loader._validate_ohlcv_bounds(df)

    def test_ohlc_bounds_high_less_than_open_rejected(self):
        """[Market Data Unit]: High < Open MUST be rejected."""
        df = pd.DataFrame([{
            "timestamp": self.now,
            "open": 100.0,
            "high": 99.0,  # Invalid: high < open
            "low": 95.0,
            "close": 98.0,
            "volume": 10.0,
        }])
        with self.assertRaises(DataValidationError):
            self.loader._validate_ohlcv_bounds(df)

    def test_ohlc_bounds_negative_volume_rejected(self):
        """[Market Data Unit]: Negative volume MUST be rejected."""
        df = pd.DataFrame([{
            "timestamp": self.now,
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": 98.0,
            "volume": -5.0,  # Invalid
        }])
        with self.assertRaises(DataValidationError):
            self.loader._validate_ohlcv_bounds(df)


if __name__ == "__main__":
    unittest.main()
