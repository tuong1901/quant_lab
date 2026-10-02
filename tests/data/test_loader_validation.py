"""
Unit tests for DatasetLoader and data validation checks (`src/market_data/loader.py`).
"""

import os
import tempfile
import unittest
import pandas as pd
from datetime import datetime, timezone

from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.dataset import DataRange, StorageReference, Dataset
from src.data.loader import DatasetLoader
from src.data.versioning import calculate_content_hash
from src.data.exceptions import DataValidationError


class TestLoaderValidation(unittest.TestCase):
    """
    [PURPOSE]: Test DatasetLoader file IO, OHLC checks, timestamp validation, and hash verification.
    """

    def setUp(self):
        self.loader = DatasetLoader()
        self.temp_dir = tempfile.TemporaryDirectory()

        self.timestamps = pd.date_range(start="2024-01-01 00:00:00+00:00", periods=5, freq="15min")
        self.df_valid = pd.DataFrame(
            {
                "timestamp": self.timestamps,
                "open": [50000.0, 50100.0, 50200.0, 50150.0, 50300.0],
                "high": [50200.0, 50300.0, 50400.0, 50350.0, 50500.0],
                "low": [49900.0, 50050.0, 50150.0, 50100.0, 50250.0],
                "close": [50100.0, 50200.0, 50150.0, 50300.0, 50450.0],
                "volume": [10.5, 12.0, 15.2, 8.4, 20.1],
            }
        )

        # Save valid parquet file
        self.valid_parquet_path = os.path.join(self.temp_dir.name, "valid.parquet")
        self.df_valid.to_parquet(self.valid_parquet_path)

        self.hash_valid = calculate_content_hash(self.df_valid)

        self.market = Market("binance", "BTCUSDT", "perpetual", "USDT")
        self.data_range = DataRange(
            start=datetime(2023, 12, 31, tzinfo=timezone.utc),
            end=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        self.storage_ref = StorageReference(type="local", path=self.valid_parquet_path)

        self.dataset_valid = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash=self.hash_valid,
            storage_reference=self.storage_ref,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_valid_dataset(self):
        """Test loading a valid dataset file successfully."""
        market_data = self.loader.load(self.dataset_valid)
        self.assertEqual(len(market_data.df), 5)
        self.assertEqual(market_data.dataset.identity, "btcusdt_binance_perp_15m:v1")

    def test_missing_file_raises_error(self):
        """Test loading non-existent file path raises DataValidationError."""
        bad_ref = StorageReference(type="local", path="non_existent_file.parquet")
        bad_ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash=self.hash_valid,
            storage_reference=bad_ref,
        )
        with self.assertRaises(DataValidationError):
            self.loader.load(bad_ds)

    def test_invalid_ohlc_high_less_than_low(self):
        """Test that high < low raises DataValidationError."""
        df_bad = self.df_valid.copy()
        df_bad.loc[0, "high"] = 48000.0  # High lower than Low (49900.0)
        bad_path = os.path.join(self.temp_dir.name, "bad_ohlc.parquet")
        df_bad.to_parquet(bad_path)

        bad_hash = calculate_content_hash(df_bad)
        bad_ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash=bad_hash,
            storage_reference=StorageReference(type="local", path=bad_path),
        )

        with self.assertRaises(DataValidationError):
            self.loader.load(bad_ds)

    def test_negative_volume_raises_error(self):
        """Test that negative volume raises DataValidationError."""
        df_bad = self.df_valid.copy()
        df_bad.loc[0, "volume"] = -5.0
        bad_path = os.path.join(self.temp_dir.name, "bad_vol.parquet")
        df_bad.to_parquet(bad_path)

        bad_hash = calculate_content_hash(df_bad)
        bad_ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash=bad_hash,
            storage_reference=StorageReference(type="local", path=bad_path),
        )

        with self.assertRaises(DataValidationError):
            self.loader.load(bad_ds)

    def test_duplicate_timestamp_raises_error(self):
        """Test that duplicate timestamps raise DataValidationError."""
        df_bad = self.df_valid.copy()
        df_bad.loc[1, "timestamp"] = df_bad.loc[0, "timestamp"]  # Duplicate timestamp
        bad_path = os.path.join(self.temp_dir.name, "dup_ts.parquet")
        df_bad.to_parquet(bad_path)

        bad_hash = calculate_content_hash(df_bad)
        bad_ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash=bad_hash,
            storage_reference=StorageReference(type="local", path=bad_path),
        )

        with self.assertRaises(DataValidationError):
            self.loader.load(bad_ds)

    def test_content_hash_mismatch_raises_error(self):
        """Test that mismatched expected content hash raises DataValidationError."""
        bad_ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="WRONG_HASH_123456",
            storage_reference=self.storage_ref,
        )
        with self.assertRaises(DataValidationError):
            self.loader.load(bad_ds)

    def test_missing_candles_detection(self):
        """Test that detect_missing_candles correctly identifies gaps without forward filling."""
        # Create timestamps with a 30m gap instead of 15m (missing 1 bar)
        ts_gap = [
            pd.Timestamp("2024-01-01 00:00:00+00:00"),
            pd.Timestamp("2024-01-01 00:15:00+00:00"),
            pd.Timestamp("2024-01-01 00:45:00+00:00"),  # Skipped 00:30
        ]
        df_gap = pd.DataFrame({"timestamp": ts_gap, "close": [1, 2, 3]})
        missing = self.loader.detect_missing_candles(df_gap, Timeframe.M15)
        self.assertEqual(missing, 1)


if __name__ == "__main__":
    unittest.main()
