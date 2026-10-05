"""Production-path proof using a bounded read-only slice of the approved real dataset."""

from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.data.dataset import DataRange, Dataset, StorageReference
from src.data.loader import DatasetLoader
from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.versioning import calculate_content_hash
from src.features.indicators import calculate_causal_atr
from src.evaluation.metrics import calculate_basic_metrics
from src.strategies.ema import EMAStrategy
from src.trading.backtest import BacktestEngine


class TestStrictDataPipelineE2E(unittest.TestCase):
    """Prove Dataset -> Feature -> Strategy -> Backtest using 64 real M15 candles."""

    def setUp(self) -> None:
        scratch_root = Path.cwd() / ".test-artifacts"
        scratch_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=scratch_root)
        source_path = Path("data/valm15-indivip_signal.csv")
        self.raw = pd.read_csv(source_path, nrows=64)
        self.fixture_path = Path(self.temp_dir.name) / "valm15_slice.csv"
        self.raw.to_csv(self.fixture_path, index=False)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_strict_dataset_reaches_evaluation(self) -> None:
        """Load real data through strict backtest and evaluate the resulting metrics."""
        timestamps = pd.to_datetime(self.raw["time"], utc=True)
        dataset = Dataset(
            dataset_id="btc_val_m15_slice",
            version="v1",
            market=Market("binance", "BTCUSDT", "USDT", "perpetual"),
            timeframe=Timeframe.M15,
            data_range=DataRange(timestamps.min().to_pydatetime(), (timestamps.max() + pd.Timedelta(minutes=15)).to_pydatetime()),
            storage_reference=StorageReference(str(self.fixture_path), "csv"),
            content_hash=calculate_content_hash(self.raw),
        )

        market_data = DatasetLoader().load(dataset)
        frame = market_data.df.copy()
        frame["atr"] = calculate_causal_atr(frame, period=14)
        frame["ema2"] = frame["close"].ewm(span=2, adjust=False).mean()
        frame["ema4"] = frame["close"].ewm(span=4, adjust=False).mean()

        result = BacktestEngine(strategy=EMAStrategy(fast_period=2, slow_period=4)).run(frame)
        metrics = calculate_basic_metrics(result)

        self.assertEqual(result.bars_processed, len(frame))
        self.assertEqual(len(result.signals), len(frame))
        self.assertEqual(market_data.dataset.content_hash, dataset.content_hash)
        self.assertEqual(metrics.final_equity, result.final_equity)
        self.assertEqual(metrics.net_pnl, result.final_equity - result.initial_capital)
        self.assertEqual(metrics.return_pct, metrics.net_pnl / metrics.initial_capital * 100.0)
        self.assertEqual(len(metrics.equity_curve), len(result.portfolio_history))
