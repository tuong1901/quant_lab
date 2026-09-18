"""
Unit tests for inter-config reference resolution in ConfigLoader (`src/config/loader.py`).
"""

import unittest
from datetime import datetime, timezone

from src.config.loader import ConfigLoader
from src.config.exceptions import ConfigReferenceError, ConfigValidationError


class TestConfigReferences(unittest.TestCase):
    """
    [PURPOSE]: Verify that ExperimentConfig correctly resolves sub-config references and raises errors on missing references.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")

    def test_load_valid_experiment_resolves_all_references(self):
        """Test loading btc_rolling_1y experiment resolves environment, datasets, execution, and portfolio references."""
        exp_cfg = self.loader.load_experiment("btc_rolling_1y")

        self.assertEqual(exp_cfg.name, "btc_rolling_1y")
        self.assertEqual(exp_cfg.environment.system.name, "quant_lab")
        self.assertEqual(exp_cfg.strategy_dataset.market.symbol, "BTCUSDT")
        self.assertEqual(exp_cfg.execution_dataset.market.symbol, "BTCUSDT")
        self.assertEqual(exp_cfg.execution.fill.model, "ltf_replay")
        self.assertEqual(exp_cfg.portfolio.account.initial_capital, 10000.0)
        self.assertEqual(exp_cfg.time.mode, "rolling")

    def test_missing_dataset_reference_raises_error(self):
        """Test that referencing a non-existent dataset raises ConfigReferenceError."""
        with self.assertRaises(ConfigReferenceError):
            self.loader.load_dataset("non_existent_dataset_name")

    def test_missing_execution_reference_raises_error(self):
        """Test that referencing a non-existent execution preset raises ConfigReferenceError."""
        with self.assertRaises(ConfigReferenceError):
            self.loader.load_execution("non_existent_execution_preset")

    def test_missing_portfolio_reference_raises_error(self):
        """Test that referencing a non-existent portfolio preset raises ConfigReferenceError."""
        with self.assertRaises(ConfigReferenceError):
            self.loader.load_portfolio("non_existent_portfolio_preset")

    def test_missing_experiment_raises_error(self):
        """Test that requesting a non-existent experiment name raises ConfigReferenceError."""
        with self.assertRaises(ConfigReferenceError):
            self.loader.load_experiment("non_existent_experiment")


if __name__ == "__main__":
    unittest.main()
