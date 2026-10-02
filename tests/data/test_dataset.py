"""
Unit tests for Dataset and DataRange models (`src/market_data/dataset.py`).
"""

import unittest
from datetime import datetime, timezone

from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.dataset import DataRange, StorageReference, Dataset
from src.data.exceptions import InvalidDatasetError


class TestDatasetModels(unittest.TestCase):
    """
    [PURPOSE]: Verify creation, immutability, serialization, and validation of Dataset and DataRange.
    """

    def setUp(self):
        self.market = Market("binance", "BTCUSDT", "perpetual", "USDT")
        self.start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.end = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.data_range = DataRange(start=self.start, end=self.end)
        self.storage_ref = StorageReference(type="local", path="data/raw/binance/BTCUSDT/15m/v3.parquet")

    def test_datarange_validations(self):
        """Test DataRange UTC requirement and start < end constraint."""
        # Naive datetime should be rejected
        naive_start = datetime(2024, 1, 1, 0, 0, 0)
        with self.assertRaises(InvalidDatasetError):
            DataRange(start=naive_start, end=self.end)

        # Invalid start >= end should be rejected
        with self.assertRaises(InvalidDatasetError):
            DataRange(start=self.end, end=self.start)

    def test_dataset_creation_and_identity(self):
        """Test Dataset creation, property identity format (dataset_id:v3), and post_init validation."""
        ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=3,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="abc123sha256hash",
            storage_reference=self.storage_ref,
        )

        self.assertEqual(ds.identity, "btcusdt_binance_perp_15m:v3")
        self.assertEqual(str(ds.timeframe), "15m")
        self.assertEqual(ds.version, 3)

    def test_dataset_immutability(self):
        """Test that Dataset attributes cannot be modified."""
        ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=3,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="abc123sha256hash",
            storage_reference=self.storage_ref,
        )
        with self.assertRaises(AttributeError):
            ds.version = 4

    def test_dataset_to_dict_and_from_dict(self):
        """Test Dataset serialization to dictionary and reconstruction."""
        ds = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=3,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="abc123sha256hash",
            storage_reference=self.storage_ref,
        )
        d = ds.to_dict()
        reconstructed = Dataset.from_dict(d)
        self.assertEqual(reconstructed.identity, ds.identity)
        self.assertEqual(reconstructed.content_hash, ds.content_hash)
        self.assertEqual(reconstructed.market, ds.market)


if __name__ == "__main__":
    unittest.main()
