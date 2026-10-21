"""Synthetic descriptor -> loader -> features -> strategy -> engine -> evaluation proof."""

from unittest.mock import mock_open, patch
import unittest
import yaml
import pandas as pd

from src.data.columns import CANONICAL_COLUMNS, ColumnPolicy
from src.data.dataset import Dataset
from src.data.loader import DatasetLoader
from src.data.versioning import calculate_content_hash
from src.data.timeframe import Timeframe
from src.features.indicators import calculate_causal_atr
from src.evaluation.metrics import calculate_basic_metrics
from src.strategies.ema import EMAStrategy
from src.trading.backtest import BacktestEngine, HistoricalClock


class TestStrictDataPipelineE2E(unittest.TestCase):
    def test_strict_dataset_reaches_evaluation(self):
        """
        [PURPOSE]: Exercise actual YAML parsing, policy, repair, hash and engine in memory.
        [DEPENDENCIES]: Strict data and trading APIs; mocked filesystem boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures logs and runs synthetic simulation.
        """
        prices = [100., 102., 104., 103., 99., 97., 101., 106.]
        raw = pd.DataFrame(dict(time=pd.date_range("2018-01-01", periods=8, freq="15min", tz="UTC"),
                                open=prices, high=[p+4 for p in prices], low=[p-4 for p in prices],
                                close=prices, Volume=1., note="synthetic"))
        mapping = {name: name for name in CANONICAL_COLUMNS}
        mapping.update(timestamp="time", volume="Volume")
        policy = ColumnPolicy(mapping, ("note",))
        with self.assertLogs("src.data", level="INFO"):
            digest = calculate_content_hash(raw, policy)
        payload = dict(dataset_id="synthetic", version="v1",
                       market=dict(venue="binance", symbol="ETHUSDT", quote_currency="USDT", market_type="perpetual"),
                       timeframe="15m", data_range=dict(start=raw.time.iloc[0].isoformat(),
                       end=(raw.time.iloc[-1]+pd.Timedelta(minutes=15)).isoformat()),
                       storage_reference=dict(path="never-read.csv", format="csv"),
                       content_hash=digest, columns=policy.to_dict())
        with patch("builtins.open", mock_open(read_data=yaml.safe_dump(payload))):
            dataset = Dataset.from_yaml("never-read.yaml")
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=raw), self.assertLogs("src.data", level="INFO") as logs:
            market_data = DatasetLoader().load(dataset)
        self.assertNotIn("note", market_data.df)
        self.assertIn("candle_repaired", "\n".join(logs.output))
        frame = market_data.df.copy()
        frame["atr"] = calculate_causal_atr(frame, period=3)
        frame["ema2"] = frame.close.ewm(span=2, adjust=False).mean()
        frame["ema4"] = frame.close.ewm(span=4, adjust=False).mean()
        engine = BacktestEngine(strategy=EMAStrategy(2, 4), symbol="ETHUSDT",
                                clock=HistoricalClock(frame.timestamp.iloc[0]))
        result = engine.run(frame)
        metrics = calculate_basic_metrics(result)
        self.assertEqual(result.bars_processed, 8)
        self.assertTrue(result.fills)
        self.assertEqual(metrics.final_equity, result.final_equity)
        self.assertTrue(all(order.symbol == "ETHUSDT" for order in result.orders))
