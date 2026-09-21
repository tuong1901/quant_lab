"""
[PURPOSE]: Unit tests for src.experiments.window using standard unittest.
[DEPENDENCIES]: unittest, datetime, src.experiments.window.
"""

import unittest
from datetime import datetime, timezone, timedelta
from src.experiments.window import TimeWindow

class TestTimeWindow(unittest.TestCase):
    def test_time_window_valid(self):
        dt_warmup = datetime(2024, 12, 29, 0, 0, tzinfo=timezone.utc)
        dt_exec_start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        dt_exec_end = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

        win = TimeWindow(
            warmup_start=dt_warmup,
            execution_start=dt_exec_start,
            execution_end=dt_exec_end
        )

        self.assertEqual(win.warmup_start, dt_warmup)
        self.assertEqual(win.execution_start, dt_exec_start)
        self.assertEqual(win.execution_end, dt_exec_end)
        self.assertEqual(win.warmup_duration, timedelta(days=3))
        self.assertEqual(win.execution_duration, timedelta(days=365))

    def test_time_window_immutability(self):
        dt_warmup = datetime(2024, 12, 29, 0, 0, tzinfo=timezone.utc)
        dt_exec_start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        dt_exec_end = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

        win = TimeWindow(
            warmup_start=dt_warmup,
            execution_start=dt_exec_start,
            execution_end=dt_exec_end
        )

        with self.assertRaises(AttributeError):
            win.execution_start = datetime(2025, 2, 1, 0, 0, tzinfo=timezone.utc)

    def test_time_window_invalid_order(self):
        dt_warmup = datetime(2025, 1, 5, 0, 0, tzinfo=timezone.utc)
        dt_exec_start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        dt_exec_end = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            TimeWindow(
                warmup_start=dt_warmup,
                execution_start=dt_exec_start,
                execution_end=dt_exec_end
            )

    def test_time_window_naive_datetime(self):
        dt_warmup = datetime(2024, 12, 29, 0, 0)  # Naive
        dt_exec_start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        dt_exec_end = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            TimeWindow(
                warmup_start=dt_warmup,
                execution_start=dt_exec_start,
                execution_end=dt_exec_end
            )

if __name__ == "__main__":
    unittest.main()
