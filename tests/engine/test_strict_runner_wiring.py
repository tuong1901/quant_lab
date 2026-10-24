"""Strict runner integration checks; no real YAML, data or log files accessed."""

from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import io
import logging
from contextlib import redirect_stdout

import pandas as pd
import numpy as np

import run_backtest as runner
from src.config.runner import BacktestRunnerConfig
from src.data.timeframe import Timeframe
from src.trading.backtest import BacktestEngine, HistoricalClock
from src.strategies.ema import EMAStrategy


class TestStrictRunnerWiring(unittest.TestCase):
    def setUp(self):
        """
        [PURPOSE]: Prepare synthetic pre-2020 ETH candles and configuration.
        [DEPENDENCIES]: pandas and config dataclass.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes test state in memory.
        """
        self.config = BacktestRunnerConfig("unused.yaml", 2, 5, None, 0., 10000., 2.,
                                           "fixed_quantity", .01, .5, 10., 50000., True,
                                           3, 3., 2., 1., 2., 4.)
        prices = [100., 102., 105., 103., 99., 96., 101., 105., 110., 108.]
        self.frame = pd.DataFrame({"timestamp": pd.date_range("2018-01-01", periods=10, freq="15min", tz="UTC"),
                                   "open": prices, "close": prices,
                                   "high": [p + 1 for p in prices], "low": [p - 1 for p in prices], "volume": 1.})
        self.dataset = SimpleNamespace(identity="synthetic_eth:v1", market=SimpleNamespace(symbol="ETHUSDT"),
                                       timeframe=Timeframe.M15)

    def run_synthetic(self, config=None):
        """
        [PURPOSE]: Execute real features, engine and evaluation behind mocked disk boundaries.
        [DEPENDENCIES]: run_strict_backtest.
        [ARGS]: config — optional settings override.
        [RETURNS]: StrictBacktestEvaluation.
        [SIDE EFFECTS]: Runs an in-memory backtest.
        """
        with patch.object(runner.Dataset, "from_yaml", return_value=self.dataset), \
             patch.object(runner.DatasetLoader, "load", return_value=SimpleNamespace(df=self.frame)):
            return runner.run_strict_backtest(config or self.config)

    def test_real_engine_uses_dataset_identity_and_pre2020_clock(self):
        """
        [PURPOSE]: Check real fills, symbols, run identity and accounting on old candles.
        [DEPENDENCIES]: Synthetic runner pipeline.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes assertions.
        """
        evaluation = self.run_synthetic()
        result = evaluation.result
        self.assertEqual(result.dataset_id, self.dataset.identity)
        self.assertEqual(result.run_id, "strict:synthetic_eth:v1")
        self.assertEqual(result.bars_processed, 10)
        self.assertTrue(result.fills)
        self.assertTrue(all(order.symbol == "ETHUSDT" for order in result.orders))
        self.assertTrue(all(fill.symbol == "ETHUSDT" for fill in result.fills))
        self.assertAlmostEqual(evaluation.accounting.residual, 0.)

    def test_atr_period_reaches_indicator_and_changes_output(self):
        """
        [PURPOSE]: Prove the configured ATR period reaches the real indicator.
        [DEPENDENCIES]: add_ema_features and synthetic runner.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures calls and checks output.
        """
        with patch.object(runner, "calculate_causal_atr", wraps=runner.calculate_causal_atr) as atr:
            self.run_synthetic(replace(self.config, atr_period=7))
            self.assertEqual(atr.call_args.kwargs, {"period": 7})
        short = runner.add_ema_features(self.frame, 2, 5, 3)["atr"]
        long = runner.add_ema_features(self.frame, 2, 5, 7)["atr"]
        self.assertFalse(np.allclose(short, long))

    def test_empty_selection_fails_before_engine_creation(self):
        """
        [PURPOSE]: Reject empty selected data with a clear error.
        [DEPENDENCIES]: Synthetic runner.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures constructor and asserts failure.
        """
        self.frame = self.frame.iloc[:0]
        with patch.object(runner, "BacktestEngine") as engine:
            with self.assertLogs("run_backtest", level="ERROR") as logs:
                with self.assertRaisesRegex(ValueError, "empty"):
                    self.run_synthetic()
            engine.assert_not_called()
            self.assertIn("unused.yaml", "\n".join(logs.output))

    def test_legacy_constructor_keeps_instrument_fallback(self):
        """
        [PURPOSE]: Preserve existing callers which use run_id as symbol.
        [DEPENDENCIES]: BacktestEngine direct constructor.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Runs synthetic simulation and asserts compatibility.
        """
        engine = BacktestEngine(strategy=EMAStrategy(2, 5), run="legacy_symbol",
                                clock=HistoricalClock(self.frame.timestamp.iloc[0]))
        result = engine.run(runner.add_ema_features(self.frame, 2, 5))
        self.assertTrue(result.orders)
        self.assertTrue(all(order.symbol == "legacy_symbol" for order in result.orders))

    def test_all_runtime_settings_reach_real_consumers(self):
        """
        [PURPOSE]: Protect constructor wiring while executing the real engine.
        [DEPENDENCIES]: Autospecced spy and synthetic pipeline.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Runs simulation and checks runtime settings.
        """
        config = replace(self.config, sizing_mode="risk_per_trade", allow_short=False, bar_limit=8)
        with patch.object(BacktestEngine, "run", autospec=True, side_effect=BacktestEngine.run) as spy:
            evaluation = self.run_synthetic(config)
        engine = spy.call_args.args[0]
        self.assertEqual(engine.portfolio.initial_capital, config.initial_capital)
        self.assertEqual(engine.portfolio.margin_model.leverage, config.leverage)
        self.assertEqual(engine.strategy.fast_period, config.fast_period)
        self.assertEqual(engine.strategy.slow_period, config.slow_period)
        self.assertEqual(engine.default_order_quantity, config.fixed_quantity)
        for name in ("sizing_mode", "risk_per_trade_pct", "max_position_size", "max_notional",
                     "allow_short", "atr_multiplier", "reward_to_risk"):
            self.assertEqual(getattr(engine, name), getattr(config, name))
        self.assertEqual(engine.execution.slippage_model.slippage_bps, config.slippage_bps)
        self.assertEqual(engine.execution.fee_model.maker_rate, config.maker_fee_bps / 10000)
        self.assertEqual(engine.execution.fee_model.taker_rate, config.taker_fee_bps / 10000)
        self.assertEqual(evaluation.result.bars_processed, 8)
        self.assertEqual(engine.clock.now(), self.frame.timestamp.iloc[7])

    def test_function_logs_include_settings_and_completion(self):
        """
        [PURPOSE]: Verify INFO summaries and DEBUG helper traces without full data dumps.
        [DEPENDENCIES]: Python logging capture and real engine.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures log records in memory.
        """
        with self.assertLogs(level="DEBUG") as logs:
            result = self.run_synthetic()
            runner.format_evaluation(result)
        functions = {record.funcName for record in logs.records}
        self.assertTrue({"run_strict_backtest", "_run_strict_backtest", "add_ema_features",
                         "__init__", "run", "_run_bars", "_get_run_id", "_entry_quantity",
                         "_set_exit_levels", "_apply_bar_exit", "format_evaluation"} <= functions)
        text = "\n".join(logs.output)
        for detail in ("synthetic_eth:v1", "ETHUSDT", "atr_period=3", "capital=10000",
                       "slippage_bps=1", "selected_rows=10", "Engine completed"):
            self.assertIn(detail, text)
        with self.assertLogs(level="INFO") as info_logs:
            self.run_synthetic()
        self.assertTrue(all(record.levelno >= logging.INFO for record in info_logs.records))
        self.assertNotIn("Processing bar", "\n".join(info_logs.output))

    def test_cli_stdout_and_failure_diagnostics(self):
        """
        [PURPOSE]: Keep reports on stdout and log configuration failures before data loading.
        [DEPENDENCIES]: Mocked CLI I/O boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures stdout and logging in memory.
        """
        result = self.run_synthetic()
        output = io.StringIO()
        with patch.object(runner, "configure_logging") as configure, \
             patch.object(runner, "load_backtest_runner_config", return_value=self.config), \
             patch.object(runner, "run_strict_backtest", return_value=result), redirect_stdout(output):
            self.assertEqual(runner.main(["--log-level", "DEBUG"]), 0)
            configure.assert_called_once_with("DEBUG")
        self.assertEqual(output.getvalue(), runner.format_evaluation(result) + "\n")
        with patch.object(runner, "configure_logging"), \
             patch.object(runner, "load_backtest_runner_config", side_effect=ValueError("invalid configuration")), \
             patch.object(runner.Dataset, "from_yaml") as read_data, \
             self.assertLogs("run_backtest", level="ERROR") as logs:
            self.assertEqual(runner.main([]), 1)
            read_data.assert_not_called()
        self.assertIn("invalid configuration", "\n".join(logs.output))

    def test_logging_setup_appends_utf8_file_and_stderr(self):
        """
        [PURPOSE]: Verify output handler configuration without touching log files.
        [DEPENDENCIES]: Mocked directory creation and logging setup.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Asserts mocked calls only.
        """
        with patch.object(runner.Path, "mkdir"), patch.object(logging, "FileHandler") as file_handler, \
             patch.object(logging, "StreamHandler") as stream_handler, \
             patch.object(logging, "basicConfig") as setup:
            runner.configure_logging("DEBUG")
        self.assertEqual(file_handler.call_args.kwargs, {"mode": "a", "encoding": "utf-8"})
        self.assertEqual(str(file_handler.call_args.args[0]), str(runner.Path("logs/backtest.log")))
        stream_handler.assert_called_once_with()
        self.assertEqual(setup.call_args.kwargs["level"], "DEBUG")
        self.assertIn("%(funcName)s", setup.call_args.kwargs["format"])
