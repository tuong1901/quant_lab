"""E2E proof that the run_backtest CLI uses the strict production path."""

from pathlib import Path
from contextlib import redirect_stdout
import io
import tempfile
import unittest

import pandas as pd

from run_backtest import format_evaluation, main, run_strict_backtest
from src.data.dataset import DataRange, Dataset, StorageReference
from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.versioning import calculate_content_hash


class TestStrictBacktestRunner(unittest.TestCase):
    """Verify Dataset YAML reaches strict execution and complete evaluation output."""

    def setUp(self) -> None:
        root = Path.cwd() / ".test-artifacts"
        root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=root)
        source = pd.read_csv(Path("data/valm15-indivip_signal.csv"), nrows=64).iloc[30:64].copy()
        fixture_path = Path(self.temp_dir.name) / "valid_m15_slice.csv"
        source.to_csv(fixture_path, index=False)
        timestamps = pd.to_datetime(source["time"], utc=True)
        dataset = Dataset(
            dataset_id="runner_e2e_m15",
            version="v1",
            market=Market("binance", "BTCUSDT", "USDT", "perpetual"),
            timeframe=Timeframe.M15,
            data_range=DataRange(
                timestamps.min().to_pydatetime(),
                (timestamps.max() + pd.Timedelta(minutes=15)).to_pydatetime(),
            ),
            storage_reference=StorageReference(str(fixture_path), "csv"),
            content_hash=calculate_content_hash(source),
        )
        self.descriptor_path = Path(self.temp_dir.name) / "runner_dataset.yaml"
        dataset.to_yaml(str(self.descriptor_path))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_runner_uses_strict_dataset_and_prints_accounting_reconciliation(self) -> None:
        """Run the strict runner from YAML and require a reconciled full evaluation output."""
        evaluation = run_strict_backtest(
            str(self.descriptor_path), fast_period=2, slow_period=4
        )
        report = format_evaluation(evaluation)

        self.assertEqual(evaluation.result.bars_processed, 34)
        self.assertAlmostEqual(evaluation.accounting.residual, 0.0)
        self.assertIn("ACCOUNTING RECONCILIATION", report)
        self.assertIn("Unrealized PnL", report)
        self.assertIn("Reconciliation residual", report)
        self.assertIn("Max drawdown", report)

    def test_cli_main_prints_the_complete_strict_evaluation(self) -> None:
        """Invoke the CLI entrypoint and require the accounting breakdown in stdout."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main([
                "--dataset-definition", str(self.descriptor_path),
                "--fast-period", "2",
                "--slow-period", "4",
            ])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("STRICT BACKTEST EVALUATION", output)
        self.assertIn("ACCOUNTING RECONCILIATION", output)
        self.assertIn("Fees paid", output)
        self.assertIn("Final equity", output)
