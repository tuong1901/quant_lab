"""
[PURPOSE]: Integrity unit tests covering execution timing, same-bar lookahead proof, clock monotonicity, boundary execution windows, HOLD-only sanity, alternating signals, and determinism.
[DEPENDENCIES]: unittest, pandas, datetime, src.engine, src.strategies, src.environment, src.engine.
"""

import unittest
from datetime import datetime, timedelta, timezone
import random
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.strategies.strategy import Strategy
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.experiments.window import TimeWindow
from src.experiments.run import ExperimentRun
from src.engine.backtest_engine import BacktestEngine
from src.evaluation.metrics import calculate_basic_metrics


class HoldOnlyStrategy(Strategy):
    """[PURPOSE]: Strategy that always returns HOLD."""
    def on_bar(self, context: StrategyContext) -> Signal:
        return Signal(timestamp=context.timestamp, action=SignalAction.HOLD, strategy_id="hold_only")


class AlternatingStrategy(Strategy):
    """[PURPOSE]: Strategy that alternates between LONG and SHORT."""
    def __init__(self):
        self.state = False

    def on_bar(self, context: StrategyContext) -> Signal:
        self.state = not self.state
        action = SignalAction.LONG if self.state else SignalAction.SHORT
        return Signal(timestamp=context.timestamp, action=action, strategy_id="alternating")


class SeededRandomStrategy(Strategy):
    """[PURPOSE]: Deterministic pseudo-random strategy using fixed seed."""
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def on_bar(self, context: StrategyContext) -> Signal:
        choices = [SignalAction.HOLD, SignalAction.LONG, SignalAction.SHORT]
        action = self.rng.choice(choices)
        return Signal(timestamp=context.timestamp, action=action, strategy_id="random")


class TestPipelineIntegrity(unittest.TestCase):
    """
    [PURPOSE]: Forensic integrity tests inspecting timing, lookahead, clock, boundaries, and determinism.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _create_synthetic_df(self, bars: int = 20) -> pd.DataFrame:
        data = []
        for i in range(bars):
            ts = self.start_time + timedelta(minutes=15 * i)
            price = 100.0 + (i * 2.0 if i % 2 == 0 else -i * 1.5)
            data.append({
                "timestamp": ts,
                "open": price - 1.0,
                "high": price + 5.0,
                "low": price - 5.0,
                "close": price,
                "volume": 100.0
            })
        return pd.DataFrame(data)

    def test_audit_no_op_hold_strategy(self):
        """[Audit #24]: HOLD-only strategy must produce 0 orders, 0 fills, 0 fees, and 0 PnL."""
        df = self._create_synthetic_df(bars=10)
        env = EnvironmentFactory.create(config=self.config)
        strat = HoldOnlyStrategy()
        engine = BacktestEngine(environment=env, strategy=strat)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 0, "HOLD-only strategy should create 0 orders")
        self.assertEqual(len(res.fills), 0, "HOLD-only strategy should create 0 fills")
        self.assertEqual(res.realized_pnl, 0.0, "Realized PnL must be 0")
        self.assertEqual(res.total_fees, 0.0, "Total fees must be 0")
        self.assertEqual(res.final_equity, res.initial_capital, "Final equity must equal initial capital")

    def test_audit_execution_timing_lookahead_proof(self):
        """[Audit #4 & #5]: Verify that market order at Bar 0 close executes on Bar 1 Open without look-ahead time travel."""
        t0 = self.start_time
        t1 = self.start_time + timedelta(minutes=15)
        df = pd.DataFrame([
            {"timestamp": t0, "open": 100.0, "high": 160.0, "low": 90.0, "close": 150.0, "volume": 100.0},
            {"timestamp": t1, "open": 155.0, "high": 160.0, "low": 150.0, "close": 158.0, "volume": 100.0},
        ])

        class SingleLongStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == t0:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=SingleLongStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 1, "Should generate 1 order at Bar 0")
        self.assertEqual(len(res.fills), 1, "Should generate 1 fill at Bar 1")
        fill = res.fills[0]

        # Verify next-bar execution invariants:
        self.assertEqual(fill.timestamp, t1, "Fill timestamp must be Bar 1 (t1)")
        self.assertGreater(fill.timestamp, res.orders[0].created_at, "Fill timestamp must be strictly after order creation time")
        self.assertAlmostEqual(fill.price, 155.0, places=1, msg="Fill price must use Bar 1 Open (155.0), NOT Bar 0 Open (100.0)")

    def test_audit_alternating_signal_accounting(self):
        """[Audit #25]: Alternating LONG/SHORT strategy accounting identity verification."""
        df = self._create_synthetic_df(bars=10)
        env = EnvironmentFactory.create(config=self.config)
        strat = AlternatingStrategy()
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertEqual(metrics.initial_capital, 10000.0)
        self.assertEqual(metrics.final_equity, res.final_equity)
        # Accounting Identity: Net PnL = final_equity - initial_capital
        self.assertAlmostEqual(metrics.net_pnl, metrics.final_equity - metrics.initial_capital, places=4)

    def test_audit_random_strategy_determinism(self):
        """[Audit #26]: Verify 100% deterministic backtest replay with seeded random strategy."""
        df = self._create_synthetic_df(bars=30)
        
        # Run 1
        env1 = EnvironmentFactory.create(config=self.config)
        strat1 = SeededRandomStrategy(seed=42)
        engine1 = BacktestEngine(environment=env1, strategy=strat1, default_order_quantity=1.0)
        res1 = engine1.run(df=df)

        # Run 2
        env2 = EnvironmentFactory.create(config=self.config)
        strat2 = SeededRandomStrategy(seed=42)
        engine2 = BacktestEngine(environment=env2, strategy=strat2, default_order_quantity=1.0)
        res2 = engine2.run(df=df)

        self.assertEqual(res1.bars_processed, res2.bars_processed)
        self.assertEqual(len(res1.orders), len(res2.orders))
        self.assertEqual(len(res1.fills), len(res2.fills))
        self.assertEqual(res1.final_equity, res2.final_equity)
        self.assertEqual(res1.realized_pnl, res2.realized_pnl)

    def test_audit_execution_window_boundaries(self):
        """[Audit #18 & #19]: Boundary enforcement for warmup and execution windows."""
        # 10 bars total: 0-2 warmup, 3-7 execution, 8-9 outside window
        timestamps = [self.start_time + timedelta(minutes=15 * i) for i in range(10)]
        data = []
        for i, ts in enumerate(timestamps):
            data.append({
                "timestamp": ts,
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 100.0,
                "volume": 10.0
            })
        df = pd.DataFrame(data)

        window = TimeWindow(
            warmup_start=timestamps[0],
            execution_start=timestamps[3],
            execution_end=timestamps[7]
        )
        run = ExperimentRun(run_id="run_window_audit", seed=42, window=window)

        # Strategy that always requests LONG
        class AlwaysLongStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                return Signal(timestamp=context.timestamp, action=SignalAction.LONG)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=AlwaysLongStrategy(), run=run)
        res = engine.run(df=df)

        # Processed bars should stop at execution_end (index 7, so 8 bars total: indices 0..7)
        self.assertEqual(res.bars_processed, 8)
        # Orders should only be created during execution phase (indices 3..7)
        order_timestamps = [o.created_at for o in res.orders]
        for ts in order_timestamps:
            self.assertGreaterEqual(ts, window.execution_start)
            self.assertLessEqual(ts, window.execution_end)


if __name__ == "__main__":
    unittest.main()
