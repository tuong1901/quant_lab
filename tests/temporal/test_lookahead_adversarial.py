"""
[PURPOSE]: Adversarial temporal look-ahead tests injecting future price shocks to verify 100% decision causality.
[DEPENDENCIES]: unittest, pandas, datetime, src.engine, src.strategies, src.environment, src.config.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.runtime.factory import EnvironmentFactory
from src.strategies.ema import EMAStrategy
from src.engine.backtest.backtest_engine import BacktestEngine


class TestLookaheadAdversarial(unittest.TestCase):
    """
    [PURPOSE]: Adversarial tests verifying that future data (T+1, T+2) never influences decisions or execution pricing at bar T.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _create_mock_df(self, future_spike: float = 0.0) -> pd.DataFrame:
        data = []
        for i in range(10):
            ts = self.start_time + timedelta(minutes=15 * i)
            p = 50000.0 + i * 10.0
            
            # Inject extreme future price shock at Bar 8 if specified
            if i == 8 and future_spike > 0:
                p += future_spike

            data.append({
                "timestamp": ts,
                "open": p,
                "high": p + 50.0,
                "low": p - 50.0,
                "close": p,
                "volume": 100.0,
                "ema20": p + 10.0,
                "ema50": p,
            })
        return pd.DataFrame(data)

    def test_future_price_spike_does_not_alter_past_signals(self):
        """[Temporal Guard]: Signals generated up to Bar T MUST be identical whether Bar T+1 has normal price or a 100,000 USD price spike."""
        df_normal = self._create_mock_df(future_spike=0.0)
        df_spike = self._create_mock_df(future_spike=100000.0)

        # Run Backtest 1 (Normal Data)
        env1 = EnvironmentFactory.create(config=self.config)
        strat1 = EMAStrategy(fast_period=20, slow_period=50)
        res1 = BacktestEngine(environment=env1, strategy=strat1).run(df_normal)

        # Run Backtest 2 (Spike Data at Bar 8)
        env2 = EnvironmentFactory.create(config=self.config)
        strat2 = EMAStrategy(fast_period=20, slow_period=50)
        res2 = BacktestEngine(environment=env2, strategy=strat2).run(df_spike)

        # Signals generated at Bars 0..7 MUST BE 100% IDENTICAL
        for idx in range(8):
            sig1 = res1.signals[idx]
            sig2 = res2.signals[idx]
            self.assertEqual(sig1.action, sig2.action, f"Causality leak detected at bar index {idx}!")

    def test_same_bar_execution_lookahead_prevention(self):
        """[Temporal Guard]: Signal generated at completed Bar T close MUST NEVER fill at Bar T Open."""
        df = self._create_mock_df()
        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        if len(res.fills) > 0 and len(res.orders) > 0:
            fill = res.fills[0]
            order = res.orders[0]
            
            # Fill timestamp MUST be strictly greater than order creation timestamp
            self.assertGreater(fill.timestamp, order.created_at, "Same-bar execution lookahead detected!")


if __name__ == "__main__":
    unittest.main()
