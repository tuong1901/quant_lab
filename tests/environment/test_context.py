"""
Unit tests for ExecutionContext operational scope (`src/environment/context.py`).
"""

import unittest
from datetime import datetime, timezone

from src.core.clock import HistoricalClock
from src.experiments.run import ExperimentRun
from src.experiments.window import TimeWindow


class TestExecutionContext(unittest.TestCase):
    """
    [PURPOSE]: Verify ExecutionContext immutability and narrow operational scope.
    """

    def setUp(self):
        self.clock = HistoricalClock(start_time=datetime(2024, 1, 1, tzinfo=timezone.utc))
        self.window = TimeWindow(
            warmup_start=datetime(2023, 12, 1, tzinfo=timezone.utc),
            execution_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            execution_end=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        self.run = ExperimentRun(run_id="run_001", seed=42, window=self.window)

    def test_execution_context_creation_and_immutability(self):
        """Test creating ExecutionContext and verifying frozen immutability constraint."""
        from src.environment.context import ExecutionContext

        ctx = ExecutionContext(
            clock=self.clock,
            run=self.run,
            dataset_id="btcusdt_binance_perp_15m:v1",
            execution_id="exec_default",
        )

        self.assertEqual(ctx.clock, self.clock)
        self.assertEqual(ctx.run, self.run)
        self.assertEqual(ctx.dataset_id, "btcusdt_binance_perp_15m:v1")

        with self.assertRaises(AttributeError):
            ctx.dataset_id = "other_dataset"


if __name__ == "__main__":
    unittest.main()
