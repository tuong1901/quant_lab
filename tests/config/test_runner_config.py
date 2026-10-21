"""Strict config boundary tests using only in-memory settings."""

from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from src.config.exceptions import ConfigValidationError
from src.config.runner import BacktestRunnerConfig, load_backtest_runner_config


def valid_config() -> BacktestRunnerConfig:
    """
    [PURPOSE]: Build synthetic valid settings without file access.
    [DEPENDENCIES]: BacktestRunnerConfig.
    [ARGS]: None.
    [RETURNS]: Valid configuration.
    [SIDE EFFECTS]: Runs config validation.
    """
    return BacktestRunnerConfig("unused.yaml", 2, 5, None, 0.0, 10000., 2.,
                                "fixed_quantity", .01, 1., 10., 50000., True,
                                3, 3., 2., 1., 2., 4.)


class TestRunnerConfig(unittest.TestCase):
    def test_invalid_numbers_rejected_for_every_numeric_field(self):
        """
        [PURPOSE]: Guard every numeric runtime setting against non-finite values.
        [DEPENDENCIES]: dataclasses.replace.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes assertions.
        """
        config = valid_config()
        names = ("risk_free_rate", "initial_capital", "leverage", "risk_per_trade_pct",
                 "fixed_quantity", "max_position_size", "max_notional", "atr_multiplier",
                 "reward_to_risk", "slippage_bps", "maker_fee_bps", "taker_fee_bps")
        for name in names:
            for value in (float("nan"), float("inf"), -float("inf"), True, "1", 10**400):
                with self.subTest(name=name, value=str(value)[:20]):
                    with self.assertRaises(ConfigValidationError):
                        replace(config, **{name: value})

    def test_valid_boundaries_and_invalid_rate(self):
        """
        [PURPOSE]: Preserve supported leverage, negative rates and zero costs.
        [DEPENDENCIES]: BacktestRunnerConfig validation.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes assertions.
        """
        config = replace(valid_config(), risk_free_rate=-.5, leverage=.5,
                         slippage_bps=0., maker_fee_bps=0., taker_fee_bps=0.)
        self.assertEqual(config.leverage, .5)
        for rate in (-1., -2.):
            with self.assertRaises(ConfigValidationError):
                replace(config, risk_free_rate=rate)

    def test_loader_validates_and_resolves_in_memory_payload(self):
        """
        [PURPOSE]: Check parsing and validation before any dataset I/O.
        [DEPENDENCIES]: Mocked YAML boundary.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures logs and executes assertions.
        """
        payload = dict(dataset_definition="datasets/fake.yaml",
                       strategy=dict(fast_period=2, slow_period=5), data=dict(bar_limit=20),
                       evaluation=dict(risk_free_rate=0), account=dict(initial_capital=10000, leverage=2),
                       risk=dict(sizing_mode="fixed_quantity", risk_per_trade_pct=.01, fixed_quantity=1,
                                 max_position_size=10, max_notional=50000, allow_short=False),
                       exit=dict(stop_loss=dict(mode="atr", atr_period=7, atr_multiplier=3),
                                 take_profit=dict(reward_to_risk=2), intrabar_priority="stop_first"),
                       execution=dict(slippage_bps=0, maker_fee_bps=2, taker_fee_bps=4))
        origin = Path.cwd() / "config" / "fake.yaml"
        with patch("src.config.runner._read_yaml_mapping", return_value=(payload, origin)):
            with self.assertLogs("src.config.runner", level="INFO") as logs:
                config = load_backtest_runner_config()
            self.assertEqual(config.atr_period, 7)
            self.assertFalse(config.allow_short)
            self.assertEqual(config.dataset_definition, str((origin.parent / "datasets/fake.yaml").resolve()))
            self.assertIn("atr_period=7", "\n".join(logs.output))
            payload["evaluation"]["risk_free_rate"] = -2
            with self.assertRaises(ConfigValidationError):
                load_backtest_runner_config()
