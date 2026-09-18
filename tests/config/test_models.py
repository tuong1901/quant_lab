"""
Unit tests for Typed Configuration Models (`src/config/models.py`).
"""

import unittest
from datetime import datetime, timezone

from src.config.models import (
    SystemConfig,
    ClockConfig,
    SlippageConfig,
    FeeConfig,
    AccountConfig,
    LeverageConfig,
    ExperimentTimeConfig,
)
from src.config.exceptions import ConfigValidationError


class TestConfigModels(unittest.TestCase):
    """
    [PURPOSE]: Verify creation, immutability, and post_init validations of typed config models.
    """

    def test_system_config_validation(self):
        """Test SystemConfig name and timezone validation."""
        sys_cfg = SystemConfig(name="quant_lab", timezone="UTC")
        self.assertEqual(sys_cfg.name, "quant_lab")

        with self.assertRaises(ConfigValidationError):
            SystemConfig(name="", timezone="UTC")

        with self.assertRaises(ConfigValidationError):
            SystemConfig(name="quant_lab", timezone="EST")

    def test_fee_and_slippage_bounds(self):
        """Test non-negative constraints on fee and slippage."""
        slip_cfg = SlippageConfig(value=0.0005)
        self.assertEqual(slip_cfg.value, 0.0005)

        with self.assertRaises(ConfigValidationError):
            SlippageConfig(value=-0.001)

        with self.assertRaises(ConfigValidationError):
            FeeConfig(maker=-0.0001, taker=0.0002)

    def test_account_and_leverage_bounds(self):
        """Test initial capital > 0 and leverage >= 1 bounds."""
        acc_cfg = AccountConfig(initial_capital=10000.0)
        self.assertEqual(acc_cfg.initial_capital, 10000.0)

        with self.assertRaises(ConfigValidationError):
            AccountConfig(initial_capital=0.0)

        with self.assertRaises(ConfigValidationError):
            LeverageConfig(value=0.5)

    def test_experiment_time_config_bounds(self):
        """Test start < end constraint for ExperimentTimeConfig."""
        now = datetime.now(timezone.utc)
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 1, tzinfo=timezone.utc)

        t_cfg = ExperimentTimeConfig(
            mode="fixed",
            start=start,
            end=end,
            resolved_anchor=now,
        )
        self.assertEqual(t_cfg.mode, "fixed")

        with self.assertRaises(ConfigValidationError):
            ExperimentTimeConfig(
                mode="fixed",
                start=end,
                end=start,
                resolved_anchor=now,
            )


if __name__ == "__main__":
    unittest.main()
