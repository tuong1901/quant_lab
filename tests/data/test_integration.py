"""
Integration test for Market & Dataset Subsystem (`src/market_data/`).
"""

import os
import tempfile
import unittest
import pandas as pd
from datetime import datetime, timezone

from src.data import (
    Market,
    Timeframe,
    DataRange,
    StorageReference,
    Dataset,
    calculate_content_hash,
    DatasetCatalog,
    DatasetLoader,
    validate_compatible_datasets,
)


class TestMarketDataIntegration(unittest.TestCase):
    """
    [PURPOSE]: Validate end-to-end flow: Market -> Dataset -> Catalog -> Loader -> Compatibility.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        # 1. Generate synthetic OHLCV data
        self.ts_strategy = pd.date_range(start="2024-01-01 00:00:00+00:00", periods=10, freq="15min")
        self.df_strat = pd.DataFrame(
            {
                "timestamp": self.ts_strategy,
                "open": [50000 + i * 10 for i in range(10)],
                "high": [50050 + i * 10 for i in range(10)],
                "low": [49950 + i * 10 for i in range(10)],
                "close": [50020 + i * 10 for i in range(10)],
                "volume": [100.0 + i for i in range(10)],
            }
        )

        self.strat_path = os.path.join(self.temp_dir.name, "strat_15m.parquet")
        self.df_strat.to_parquet(self.strat_path)
        self.hash_strat = calculate_content_hash(self.df_strat)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_market_data_pipeline(self):
        """Test full pipeline from Market instantiation to dataset retrieval and loader verification."""
        # Step 1: Define Market
        market = Market(
            venue="binance",
            symbol="BTCUSDT",
            market_type="perpetual",
            quote_currency="USDT",
        )
        self.assertEqual(market.identity, "binance:BTCUSDT:perpetual:USDT")

        # Step 2: Define Dataset metadata
        data_range = DataRange(
            start=datetime(2023, 12, 31, tzinfo=timezone.utc),
            end=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )
        storage_ref = StorageReference(type="local", path=self.strat_path)

        dataset = Dataset(
            dataset_id="btcusdt_binance_perp_15m",
            market=market,
            timeframe=Timeframe.M15,
            version=3,
            data_range=data_range,
            source={"provider": "binance"},
            content_hash=self.hash_strat,
            storage_reference=storage_ref,
        )

        # Step 3: Register in Catalog
        catalog = DatasetCatalog()
        catalog.register(dataset)
        self.assertTrue(catalog.exists("btcusdt_binance_perp_15m", 3))

        # Step 4: Retrieve from Catalog
        retrieved_ds = catalog.get("btcusdt_binance_perp_15m", 3)
        self.assertEqual(retrieved_ds.identity, "btcusdt_binance_perp_15m:v3")

        # Step 5: Load MarketData via Loader
        loader = DatasetLoader()
        market_data = loader.load(retrieved_ds)
        self.assertEqual(len(market_data.df), 10)
        self.assertEqual(market_data.dataset.content_hash, self.hash_strat)

        # Step 6: Validate LTF execution dataset compatibility
        exec_ds = Dataset(
            dataset_id="btcusdt_binance_perp_1m",
            market=market,
            timeframe=Timeframe.M1,
            version=7,
            data_range=data_range,
            source={"provider": "binance"},
            content_hash="dummy_hash_1m",
            storage_reference=storage_ref,
        )
        self.assertTrue(validate_compatible_datasets(retrieved_ds, exec_ds))


if __name__ == "__main__":
    unittest.main()
