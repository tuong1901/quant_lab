"""
Unit tests for DatasetCatalog registry (`src/market_data/catalog.py`).
"""

import unittest
from datetime import datetime, timezone

from src.market_data.market import Market
from src.market_data.timeframe import Timeframe
from src.market_data.dataset import DataRange, StorageReference, Dataset
from src.market_data.catalog import DatasetCatalog
from src.market_data.exceptions import DatasetNotFoundError, DuplicateDatasetError, CatalogError


class TestCatalog(unittest.TestCase):
    """
    [PURPOSE]: Verify dataset registration, lookup, version listing, and duplicate prevention.
    """

    def setUp(self):
        self.catalog = DatasetCatalog()
        self.market = Market("binance", "BTCUSDT", "perpetual", "USDT")
        self.data_range = DataRange(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        self.storage_ref = StorageReference(type="local", path="data/raw/binance/BTCUSDT/15m/v1.parquet")

        self.ds_v1 = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=1,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="hash_v1",
            storage_reference=self.storage_ref,
        )

        self.ds_v2 = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market,
            timeframe=Timeframe.M15,
            version=2,
            data_range=self.data_range,
            source={"provider": "binance"},
            content_hash="hash_v2",
            storage_reference=self.storage_ref,
        )

    def test_register_and_get_dataset(self):
        """Test registering and retrieving dataset by dataset_id and version."""
        self.catalog.register(self.ds_v1)
        self.assertTrue(self.catalog.exists("btcusdt_binance_perp_15m", 1))

        retrieved = self.catalog.get("btcusdt_binance_perp_15m", 1)
        self.assertEqual(retrieved.identity, "btcusdt_binance_perp_15m:v1")
        self.assertEqual(retrieved.content_hash, "hash_v1")

    def test_duplicate_registration_error(self):
        """Test that registering duplicate dataset identity raises DuplicateDatasetError."""
        self.catalog.register(self.ds_v1)
        with self.assertRaises(DuplicateDatasetError):
            self.catalog.register(self.ds_v1)

    def test_get_unknown_dataset_error(self):
        """Test that looking up unregistered dataset raises DatasetNotFoundError."""
        with self.assertRaises(DatasetNotFoundError):
            self.catalog.get("unknown_dataset", 1)

    def test_list_versions(self):
        """Test listing all available versions for a dataset_id in ascending order."""
        self.catalog.register(self.ds_v2)
        self.catalog.register(self.ds_v1)

        versions = self.catalog.list_versions("btcusdt_binance_perp_15m")
        self.assertEqual(versions, [1, 2])

    def test_list_all_datasets(self):
        """Test listing all registered Dataset objects."""
        self.catalog.register(self.ds_v1)
        self.catalog.register(self.ds_v2)
        all_ds = self.catalog.list()
        self.assertEqual(len(all_ds), 2)

    def test_load_catalog_from_dir(self):
        """Test scanning config/datasets/ directory and loading dataset YAML files."""
        dir_catalog = DatasetCatalog()
        count = dir_catalog.load_from_dir("config/datasets")
        self.assertGreaterEqual(count, 2)
        self.assertTrue(dir_catalog.exists("btcusdt_binance_perp_15m", 1))
        self.assertTrue(dir_catalog.exists("btcusdt_binance_perp_1m", 1))


if __name__ == "__main__":
    unittest.main()

