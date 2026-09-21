"""
Unit tests for Dataset compatibility validation (`src/market_data/compatibility.py`).
"""

import unittest
from datetime import datetime, timezone

from src.market_data.market import Market
from src.market_data.timeframe import Timeframe
from src.market_data.dataset import DataRange, StorageReference, Dataset
from src.market_data.compatibility import validate_compatible_datasets
from src.market_data.exceptions import IncompatibleDatasetError


class TestCompatibility(unittest.TestCase):
    """
    [PURPOSE]: Verify strategy vs LTF execution dataset compatibility checks.
    """

    def setUp(self):
        self.market_btc = Market("binance", "BTCUSDT", "perpetual", "USDT")
        self.market_eth = Market("binance", "ETHUSDT", "perpetual", "USDT")
        self.market_spot = Market("binance", "BTCUSDT", "spot", "USDT")

        self.range1 = DataRange(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

        self.range_no_overlap = DataRange(
            start=datetime(2025, 6, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        self.storage_ref = StorageReference(type="local", path="dummy.parquet")

        self.ds_strategy = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=self.market_btc,
            timeframe=Timeframe.M15,
            version=3,
            data_range=self.range1,
            source={"provider": "binance"},
            content_hash="hash15m",
            storage_reference=self.storage_ref,
        )

        self.ds_execution = Dataset(
            dataset_id="btcusdt_binance_perp_1m",
            market=self.market_btc,
            timeframe=Timeframe.M1,
            version=7,
            data_range=self.range1,
            source={"provider": "binance"},
            content_hash="hash1m",
            storage_reference=self.storage_ref,
        )

    def test_compatible_strategy_and_execution_datasets(self):
        """Test that same market M15 strategy and M1 execution datasets are compatible."""
        self.assertTrue(validate_compatible_datasets(self.ds_strategy, self.ds_execution))

    def test_symbol_mismatch_rejected(self):
        """Test that different symbols raise IncompatibleDatasetError."""
        ds_eth_exec = Dataset(
            dataset_id="ethusdt_binance_perp_1m",
            market=self.market_eth,
            timeframe=Timeframe.M1,
            version=1,
            data_range=self.range1,
            source={"provider": "binance"},
            content_hash="hash_eth",
            storage_reference=self.storage_ref,
        )

        with self.assertRaises(IncompatibleDatasetError):
            validate_compatible_datasets(self.ds_strategy, ds_eth_exec)

    def test_market_type_mismatch_rejected(self):
        """Test that spot vs perpetual mismatch raises IncompatibleDatasetError."""
        ds_spot_exec = Dataset(
            dataset_id="btcusdt_binance_spot_1m",
            market=self.market_spot,
            timeframe=Timeframe.M1,
            version=1,
            data_range=self.range1,
            source={"provider": "binance"},
            content_hash="hash_spot",
            storage_reference=self.storage_ref,
        )

        with self.assertRaises(IncompatibleDatasetError):
            validate_compatible_datasets(self.ds_strategy, ds_spot_exec)

    def test_no_date_overlap_rejected(self):
        """Test that non-overlapping date ranges raise IncompatibleDatasetError."""
        ds_no_overlap_exec = Dataset(
            dataset_id="btcusdt_binance_perp_1m",
            market=self.market_btc,
            timeframe=Timeframe.M1,
            version=7,
            data_range=self.range_no_overlap,
            source={"provider": "binance"},
            content_hash="hash1m_late",
            storage_reference=self.storage_ref,
        )

        with self.assertRaises(IncompatibleDatasetError):
            validate_compatible_datasets(self.ds_strategy, ds_no_overlap_exec)


if __name__ == "__main__":
    unittest.main()
