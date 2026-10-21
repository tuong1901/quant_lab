"""Synthetic CLI checks with real descriptor parsing, loader and engine."""

from contextlib import redirect_stdout
from unittest.mock import mock_open, patch
import io
import unittest
import yaml
import pandas as pd

import run_backtest as runner
from src.config.runner import BacktestRunnerConfig
from src.data.columns import CANONICAL_COLUMNS, ColumnPolicy
from src.data.versioning import calculate_content_hash


class TestStrictBacktestRunner(unittest.TestCase):
    def setUp(self):
        """
        [PURPOSE]: Prepare synthetic aliased data and explicit YAML descriptor content.
        [DEPENDENCIES]: pandas, ColumnPolicy and BacktestRunnerConfig.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes in-memory fields and captures hash repair logs.
        """
        prices = [100., 102., 104., 103., 99., 97., 101., 106.]
        self.raw = pd.DataFrame(dict(time=pd.date_range("2018-01-01", periods=8, freq="15min", tz="UTC"),
                                    open=prices, high=[p+4 for p in prices], low=[p-4 for p in prices],
                                    close=prices, Volume=1., Signal="unused"))
        mapping = {name: name for name in CANONICAL_COLUMNS}
        mapping.update(timestamp="time", volume="Volume")
        policy = ColumnPolicy(mapping, ("Signal",))
        with self.assertLogs("src.data", level="INFO"):
            digest = calculate_content_hash(self.raw, policy)
        payload = dict(dataset_id="synthetic_runner", version="v1",
                       market=dict(venue="binance", symbol="ETHUSDT", quote_currency="USDT", market_type="perpetual"),
                       timeframe="15m", data_range=dict(start=self.raw.time.iloc[0].isoformat(),
                       end=(self.raw.time.iloc[-1]+pd.Timedelta(minutes=15)).isoformat()),
                       storage_reference=dict(path="never-read.csv", format="csv"),
                       content_hash=digest, columns=policy.to_dict())
        self.yaml_text = yaml.safe_dump(payload)
        self.config = BacktestRunnerConfig("never-read.yaml", 2, 4, None, 0., 10000., 2.,
                                           "fixed_quantity", .01, .1, 1., 50000., True,
                                           3, 3., 2., 1., 2., 4.)

    def test_runner_uses_strict_dataset_and_prints_accounting_reconciliation(self):
        """
        [PURPOSE]: Exercise the complete runner behind mocked physical file access.
        [DEPENDENCIES]: run_strict_backtest and actual data/trading/evaluation APIs.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures logs and validates synthetic result.
        """
        with patch("builtins.open", mock_open(read_data=self.yaml_text)), \
             patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=self.raw), self.assertLogs(level="INFO"):
            evaluation = runner.run_strict_backtest(self.config)
        report = runner.format_evaluation(evaluation)
        self.assertEqual(evaluation.result.bars_processed, 8)
        self.assertAlmostEqual(evaluation.accounting.residual, 0.)
        self.assertEqual(evaluation.result.dataset_id, "synthetic_runner:v1")
        self.assertIn("ACCOUNTING RECONCILIATION", report)
        self.assertIn("Max drawdown", report)

    def test_cli_main_prints_the_complete_strict_evaluation(self):
        """
        [PURPOSE]: Confirm CLI reports and per-repair warnings with explicit column policy.
        [DEPENDENCIES]: main; mocked logging setup and file boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures stdout and logs in memory.
        """
        stdout = io.StringIO()
        with patch("builtins.open", mock_open(read_data=self.yaml_text)), \
             patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=self.raw), \
             patch.object(runner, "configure_logging"), \
             patch.object(runner, "load_backtest_runner_config", return_value=self.config), \
             redirect_stdout(stdout), self.assertLogs(level="INFO") as logs:
            code = runner.main([])
        self.assertEqual(code, 0)
        self.assertIn("STRICT BACKTEST EVALUATION", stdout.getvalue())
        self.assertIn("candle_repaired", "\n".join(logs.output))
        self.assertIn("Columns ignored", "\n".join(logs.output))
