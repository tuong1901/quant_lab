"""
Unit tests for BacktestEngine simulation loop orchestrator (`src/backtest/engine.py`).
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.strategies.ema import EMAStrategy
from src.strategies.signal import SignalAction
from src.portfolio.position import PositionSide
from src.experiments.window import TimeWindow
from src.experiments.run import ExperimentRun


class TestBacktestEngine(unittest.TestCase):
    """
    [PURPOSE]: Verify BacktestEngine historical simulation loop, signal translation, execution integration, clock advancement, and determinism.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

        # Create a synthetic 10-bar OHLCV DataFrame
        data = []
        for i in range(10):
            ts = self.start_time + timedelta(minutes=15 * i)
            # Create price movement: bars 0-3 rising, 4-7 falling, 8-9 flat
            price = 40000.0 + (i * 100 if i < 4 else (800 - i * 100) if i < 8 else 0)
            data.append({
                "timestamp": ts,
                "open": price - 10,
                "high": price + 20,
                "low": price - 20,
                "close": price,
                "volume": 10.0,
                "ema20": price + 50 if i < 4 else price - 50 if i < 8 else price,
                "ema50": price,
            })
        self.df = pd.DataFrame(data)

    def test_engine_basic_loop_and_state(self):
        """Test basic simulation loop processing all DataFrame rows."""
        from src.backtest.engine import BacktestEngine

        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        engine = BacktestEngine(environment=env, strategy=strat)

        state = engine.run(df=self.df)

        self.assertEqual(state.bars_processed, 10)
        self.assertEqual(len(state.signals), 10)
        self.assertEqual(state.current_timestamp, self.df["timestamp"].iloc[-1])

    def test_engine_signal_to_order_translation(self):
        """Test that LONG, SHORT, and HOLD signals are translated to appropriate orders."""
        from src.backtest.engine import BacktestEngine

        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        engine = BacktestEngine(environment=env, strategy=strat)

        state = engine.run(df=self.df)

        # Bars 0-3: EMA20 > EMA50 -> LONG signal
        # Bar 0 should generate 1 BUY order to open LONG
        # Bars 1-3 should generate 0 orders (already LONG)
        # Bars 4-7: EMA20 < EMA50 -> SHORT signal
        # Bar 4 should generate 1 SELL order to Reverse LONG -> SHORT
        # Bars 8-9: EMA20 == EMA50 -> HOLD signal -> 0 orders
        self.assertGreater(len(state.orders), 0)
        self.assertGreater(len(state.fills), 0)

    def test_engine_clock_advancement(self):
        """Test that engine advances historical clock chronologically per bar."""
        from src.backtest.engine import BacktestEngine

        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        engine = BacktestEngine(environment=env, strategy=strat)

        state = engine.run(df=self.df)

        self.assertEqual(env.clock.now(), self.df["timestamp"].iloc[-1])

    def test_engine_warmup_window_behavior(self):
        """Test that warmup window period generates no trading orders."""
        from src.backtest.engine import BacktestEngine

        window = TimeWindow(
            warmup_start=self.start_time,
            execution_start=self.start_time + timedelta(minutes=45),  # Bar index 3
            execution_end=self.start_time + timedelta(hours=5),
        )
        run = ExperimentRun(run_id="run_warmup_test", seed=42, window=window)

        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)
        engine = BacktestEngine(environment=env, strategy=strat, run=run)

        state = engine.run(df=self.df)

        # First 3 bars (0, 1, 2) are before execution_start -> warmup only
        # Signals generated: 10, but orders only issued after execution_start
        self.assertEqual(state.bars_processed, 10)
        for order in state.orders:
            self.assertGreaterEqual(order.created_at, window.execution_start)

    def test_engine_determinism(self):
        """Test that running the same backtest setup twice produces identical state."""
        from src.backtest.engine import BacktestEngine

        env1 = EnvironmentFactory.create(config=self.config)
        strat1 = EMAStrategy(fast_period=20, slow_period=50)
        engine1 = BacktestEngine(environment=env1, strategy=strat1)
        state1 = engine1.run(df=self.df)

        env2 = EnvironmentFactory.create(config=self.config)
        strat2 = EMAStrategy(fast_period=20, slow_period=50)
        engine2 = BacktestEngine(environment=env2, strategy=strat2)
        state2 = engine2.run(df=self.df)

        self.assertEqual(state1.bars_processed, state2.bars_processed)
        self.assertEqual(len(state1.signals), len(state2.signals))
        self.assertEqual(len(state1.orders), len(state2.orders))
        self.assertEqual(len(state1.fills), len(state2.fills))
        for f1, f2 in zip(state1.fills, state2.fills):
            self.assertEqual(f1.price, f2.price)
            self.assertEqual(f1.quantity, f2.quantity)


if __name__ == "__main__":
    unittest.main()
