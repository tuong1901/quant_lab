"""
Unit tests for Core primitive types and temporal UTC validation (`src/core/types.py`).
"""

import unittest
from datetime import datetime, timezone


class TestCoreTypes(unittest.TestCase):
    """
    [PURPOSE]: Verify UTC timestamp enforcement and primitive type helpers.
    """

    def test_validate_utc_timestamp_valid(self):
        """Test valid UTC-aware datetime passes validation."""
        from src.core.types import validate_utc_timestamp

        valid_dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = validate_utc_timestamp(valid_dt)
        self.assertEqual(result, valid_dt)

    def test_validate_utc_timestamp_rejects_naive(self):
        """Test naive datetime without timezone info is strictly rejected."""
        from src.core.types import validate_utc_timestamp
        from src.core.exceptions import QuantSystemError

        naive_dt = datetime(2026, 1, 1, 12, 0, 0)
        with self.assertRaises((QuantSystemError, ValueError)):
            validate_utc_timestamp(naive_dt)

    def test_create_utc_timestamp_from_iso_string(self):
        """Test creating UTC timestamp from ISO 8601 string representation."""
        from src.core.types import create_utc_timestamp

        dt_str = "2026-09-18T15:30:00Z"
        ts = create_utc_timestamp(dt_str)
        self.assertEqual(ts.year, 2026)
        self.assertEqual(ts.month, 9)
        self.assertEqual(ts.day, 18)
        self.assertEqual(ts.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
