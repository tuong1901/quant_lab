"""
[PURPOSE]: Golden fixture regression tests comparing system output against hand-derived baseline values.
[DEPENDENCIES]: unittest, pandas, datetime, src.engine, src.strategies, src.environment, src.config.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.runtime.factory import EnvironmentFactory
from src.strategies.ema import EMAStrategy
from src.engine.backtest.backtest_engine import BacktestEngine


class TestGoldenFixtures(unittest.TestCase):
    """
    [PURPOSE]: Regression tests against hand-calculated golden fixtures.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_golden_5_bar_ema_simulation(self):
        """[Regression]: 5-bar simulation with hand-reasoned EMA crossover signals."""
        data = []
        prices = [50000.0, 50100.0, 50200.0, 50300.0, 50400.0]
        # EMA20 > EMA50 for bars 0..4
        for i, p in enumerate(prices):
            ts = self.start_time + timedelta(minutes=15 * i)
            data.append({
                "timestamp": ts,
                "open": p,
                "high": p + 10.0,
                "low": p - 10.0,
                "close": p,
                "volume": 100.0,
                "ema20": p + 50.0,
                "ema50": p,
            })
        df = pd.DataFrame(data)

        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        self.assertEqual(res.bars_processed, 5)
        # All 5 bars should generate LONG signals because ema20 > ema50
        for sig in res.signals:
            self.assertEqual(sig.action.name, "LONG")


if __name__ == "__main__":
    unittest.main()
