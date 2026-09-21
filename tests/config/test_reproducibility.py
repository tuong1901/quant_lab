"""
Unit tests for deterministic 'now' anchor resolution and Config Snapshotting (`src/config/loader.py`).
"""

import os
import tempfile
import unittest
from datetime import datetime, timezone
import yaml

from src.config.loader import ConfigLoader


class TestConfigReproducibility(unittest.TestCase):
    """
    [PURPOSE]: Verify that 'now' is resolved deterministically and config snapshots preserve exact state.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_deterministic_now_resolution(self):
        """Test that anchor_now parameter deterministically sets the 'end' and 'resolved_anchor' timestamp when end=now."""
        fixed_anchor = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
        exp_cfg = self.loader.load_experiment("btc_rolling_1y", anchor_now=fixed_anchor)

        self.assertEqual(exp_cfg.time.resolved_anchor, fixed_anchor)
        self.assertEqual(exp_cfg.time.end, fixed_anchor)

    def test_snapshot_experiment_preserves_resolved_state(self):
        """Test snapshot_experiment writes config_snapshot.yaml with exact resolved fields."""
        fixed_anchor = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
        exp_cfg = self.loader.load_experiment("btc_rolling_1y", anchor_now=fixed_anchor)

        snapshot_path = self.loader.snapshot_experiment(exp_cfg, output_dir=self.temp_dir.name)
        self.assertTrue(os.path.exists(snapshot_path))

        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = yaml.safe_load(f)

        self.assertEqual(snapshot_data["experiment_name"], "btc_rolling_1y")
        self.assertEqual(snapshot_data["resolved_anchor"], fixed_anchor.isoformat())
        self.assertEqual(snapshot_data["strategy_dataset"]["identity"], "btcusdt_binance_perp_15m:v1")


if __name__ == "__main__":
    unittest.main()
