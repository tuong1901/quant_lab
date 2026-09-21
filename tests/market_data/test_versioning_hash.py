"""
Unit tests for Dataset versioning and content hashing (`src/market_data/versioning.py`).
"""

import unittest
import pandas as pd
from datetime import datetime, timezone

from src.market_data.versioning import calculate_content_hash, verify_dataset_hash
from src.market_data.exceptions import DataValidationError


class TestVersioningHash(unittest.TestCase):
    """
    [PURPOSE]: Verify deterministic content hash computation and sensitivity to data changes.
    """

    def setUp(self):
        self.timestamps = pd.date_range(start="2024-01-01 00:00:00+00:00", periods=5, freq="15min")
        self.df1 = pd.DataFrame(
            {
                "timestamp": self.timestamps,
                "open": [50000.0, 50100.0, 50200.0, 50150.0, 50300.0],
                "high": [50200.0, 50300.0, 50400.0, 50350.0, 50500.0],
                "low": [49900.0, 50050.0, 50150.0, 50100.0, 50250.0],
                "close": [50100.0, 50200.0, 50150.0, 50300.0, 50450.0],
                "volume": [10.5, 12.0, 15.2, 8.4, 20.1],
            }
        )

    def test_same_data_same_hash(self):
        """Test that identical data produces identical hash (determinism)."""
        hash1 = calculate_content_hash(self.df1)
        hash2 = calculate_content_hash(self.df1.copy())
        self.assertEqual(hash1, hash2)
        self.assertTrue(verify_dataset_hash(self.df1, hash1))

    def test_column_order_independence(self):
        """Test that reordering columns does not alter content hash."""
        reordered_df = self.df1[["volume", "close", "high", "low", "open", "timestamp"]]
        hash1 = calculate_content_hash(self.df1)
        hash2 = calculate_content_hash(reordered_df)
        self.assertEqual(hash1, hash2)

    def test_changed_data_different_hash(self):
        """Test that mutating a single price point produces a different hash."""
        modified_df = self.df1.copy()
        modified_df.loc[0, "close"] = 50100.5
        hash1 = calculate_content_hash(self.df1)
        hash2 = calculate_content_hash(modified_df)
        self.assertNotEqual(hash1, hash2)
        self.assertFalse(verify_dataset_hash(modified_df, hash1))

    def test_empty_dataframe_raises(self):
        """Test that empty DataFrame raises DataValidationError."""
        with self.assertRaises(DataValidationError):
            calculate_content_hash(pd.DataFrame())


if __name__ == "__main__":
    unittest.main()
