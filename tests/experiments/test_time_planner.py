"""
[PURPOSE]: Unit tests for src.experiments.planner using standard unittest.
[DEPENDENCIES]: unittest, datetime, src.experiments.
"""

import unittest
from datetime import datetime, timezone, timedelta
from src.experiments import (
    TimeConfig,
    Duration,
    DurationUnit,
    TimePlanner,
    DatasetRange,
    PlanningError,
)

class TestTimePlanner(unittest.TestCase):
    def test_fixed_mode_planning(self):
        ds = DatasetRange(
            start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc),
            timeframe_minutes=15
        )

        cfg = TimeConfig(
            mode="fixed",
            range_start="2025-01-01",
            range_end="2026-01-01",
            anchor="now",
            window_duration=Duration(1, DurationUnit.YEARS),
            warmup_duration=Duration(200, DurationUnit.BARS),
            freeze_anchor=True
        )

        planner = TimePlanner()
        now_dt = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
        runs = planner.plan(cfg, ds, now=now_dt)

        self.assertEqual(len(runs), 1)
        run = runs[0]
        self.assertEqual(run.run_id, "run_001")
        self.assertEqual(run.window.execution_start, datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(run.window.execution_end, datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
        # Warmup 200 bars * 15m = 3000 minutes = 50 hours
        expected_warmup_start = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc) - timedelta(hours=50)
        self.assertEqual(run.window.warmup_start, expected_warmup_start)

    def test_rolling_mode_planning(self):
        ds = DatasetRange(
            start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc),
            timeframe_minutes=15
        )

        cfg = TimeConfig(
            mode="rolling",
            range_start="2024-01-01",
            range_end="2025-06-01",
            anchor="now",
            window_duration=Duration(1, DurationUnit.YEARS),
            step_duration=Duration(1, DurationUnit.MONTHS),
            warmup_duration=Duration(200, DurationUnit.BARS),
            freeze_anchor=True
        )

        planner = TimePlanner()
        now_dt = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
        runs = planner.plan(cfg, ds, now=now_dt)

        self.assertTrue(len(runs) > 1)
        self.assertEqual(runs[0].run_id, "run_001")
        self.assertEqual(runs[1].run_id, "run_002")
        self.assertEqual(runs[1].window.execution_start, runs[0].window.execution_start + timedelta(days=30))

    def test_boundary_exceeded_error(self):
        # Dataset only starts from 2024-06-01
        ds = DatasetRange(
            start=datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc),
            timeframe_minutes=15
        )

        # Config asks for 2024-01-01 start (which is earlier than dataset start)
        cfg = TimeConfig(
            mode="fixed",
            range_start="2024-01-01",
            range_end="2025-01-01",
            anchor="now",
            window_duration=Duration(1, DurationUnit.YEARS),
            warmup_duration=Duration(200, DurationUnit.BARS),
            freeze_anchor=True
        )

        planner = TimePlanner()
        now_dt = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)

        with self.assertRaises(PlanningError):
            planner.plan(cfg, ds, now=now_dt)

    def test_frozen_anchor_reproducibility(self):
        ds = DatasetRange(
            start=datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc),
            timeframe_minutes=15
        )

        cfg = TimeConfig(
            mode="fixed",
            range_start="2024-01-01",
            range_end="now",
            anchor="now",
            window_duration=Duration(1, DurationUnit.YEARS),
            warmup_duration=Duration(200, DurationUnit.BARS),
            freeze_anchor=True
        )

        planner = TimePlanner()
        frozen_now = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)

        runs_1 = planner.plan(cfg, ds, now=frozen_now)
        runs_2 = planner.plan(cfg, ds, now=frozen_now)

        self.assertEqual(runs_1, runs_2)
        self.assertEqual(runs_1[0].window.execution_end, runs_2[0].window.execution_end)

if __name__ == "__main__":
    unittest.main()
