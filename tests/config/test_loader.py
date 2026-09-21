"""
Unit tests for ConfigLoader engine (`src/config/loader.py`).
"""

import os
import tempfile
import unittest

from src.config.loader import ConfigLoader
from src.config.exceptions import ConfigFileNotFoundError, ConfigParseError


class TestConfigLoader(unittest.TestCase):
    """
    [PURPOSE]: Verify loading default.yaml, datasets.yaml, execution.yaml, portfolio.yaml, experiments.yaml.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")

    def test_load_default_env(self):
        """Test loading system default environment config."""
        env_cfg = self.loader.load_default_env("default")
        self.assertEqual(env_cfg.system.name, "quant_lab")
        self.assertEqual(env_cfg.clock.mode, "historical")
        self.assertEqual(env_cfg.reproducibility.seed, 42)

    def test_load_dataset_preset(self):
        """Test loading named dataset configuration from datasets.yaml."""
        ds_cfg = self.loader.load_dataset("btcusdt_15m")
        self.assertEqual(ds_cfg.name, "btcusdt_15m")
        self.assertEqual(ds_cfg.market.symbol, "BTCUSDT")
        self.assertEqual(str(ds_cfg.timeframe), "15m")

    def test_load_execution_preset(self):
        """Test loading execution configuration from execution.yaml."""
        exec_cfg = self.loader.load_execution("default")
        self.assertEqual(exec_cfg.name, "default")
        self.assertEqual(exec_cfg.fill.model, "ltf_replay")

    def test_load_portfolio_preset(self):
        """Test loading portfolio configuration from portfolio.yaml."""
        port_cfg = self.loader.load_portfolio("default")
        self.assertEqual(port_cfg.name, "default")
        self.assertEqual(port_cfg.account.initial_capital, 10000.0)

    def test_missing_config_dir_raises_file_not_found(self):
        """Test that non-existent config directory raises ConfigFileNotFoundError."""
        bad_loader = ConfigLoader(config_dir="non_existent_config_dir")
        with self.assertRaises(ConfigFileNotFoundError):
            bad_loader.load_default_env("default")


if __name__ == "__main__":
    unittest.main()
