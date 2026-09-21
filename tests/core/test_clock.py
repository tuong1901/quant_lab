"""
Unit tests for Clock abstraction and implementations (`src/core/clock.py`).
"""

import unittest
from datetime import datetime, timezone, timedelta


class TestCoreClock(unittest.TestCase):
    """
    [PURPOSE]: Verify HistoricalClock simulation advancement and RealtimeClock UTC contracts.
    """

    def test_historical_clock_initialization_and_now(self):
        """Test HistoricalClock initialization and reading simulated now()."""
        from src.core.clock import HistoricalClock

        start_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        clock = HistoricalClock(start_time=start_dt)
        self.assertEqual(clock.now(), start_dt)

    def test_historical_clock_advance_to_valid(self):
        """Test advancing HistoricalClock forward in time."""
        from src.core.clock import HistoricalClock

        start_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        clock = HistoricalClock(start_time=start_dt)

        next_dt = datetime(2024, 1, 1, 0, 15, 0, tzinfo=timezone.utc)
        clock.advance_to(next_dt)
        self.assertEqual(clock.now(), next_dt)

    def test_historical_clock_advance_backward_raises_error(self):
        """Test that attempting to advance HistoricalClock backward in time raises error."""
        from src.core.clock import HistoricalClock
        from src.core.exceptions import QuantSystemError

        start_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = HistoricalClock(start_time=start_dt)

        past_dt = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        with self.assertRaises((QuantSystemError, ValueError)):
            clock.advance_to(past_dt)

    def test_realtime_clock_returns_utc_now(self):
        """Test RealtimeClock returns a valid UTC timezone-aware datetime."""
        from src.core.clock import RealtimeClock

        clock = RealtimeClock()
        ts = clock.now()
        self.assertIsInstance(ts, datetime)
        self.assertEqual(ts.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
