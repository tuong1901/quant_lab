"""
[PURPOSE]: Dedicated regression and temporal invariant unit tests proving look-ahead removal (orders execute at Bar T+1 Open).
[DEPENDENCIES]: unittest, pandas, datetime, src.backtest, src.strategies, src.environment, src.execution.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.strategies.strategy import Strategy
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.backtest.engine import BacktestEngine
from src.portfolio.position import PositionSide


class TestLookAheadExecutionTiming(unittest.TestCase):
    """
    [PURPOSE]: Verify that orders generated on Bar T Close execute strictly on Bar T+1 Open without look-ahead time travel.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_critical_lookahead_prevention_synthetic_data(self):
        """[Spec Section 7]: Bar 1 Close=200 triggers LONG order. Must NOT fill on Bar 1. Must fill on Bar 2 at Open=201."""
        t0 = self.start_time
        t1 = self.start_time + timedelta(minutes=15)
        t2 = self.start_time + timedelta(minutes=30)

        data = [
            {"timestamp": t0, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10.0},
            {"timestamp": t1, "open": 100.0, "high": 201.0, "low": 99.0, "close": 200.0, "volume": 10.0},
            {"timestamp": t2, "open": 201.0, "high": 202.0, "low": 200.0, "close": 201.0, "volume": 10.0},
        ]
        df = pd.DataFrame(data)

        class BreakoutStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.price > 150.0:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=BreakoutStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 1, "Should generate 1 order on Bar 1")
        self.assertEqual(len(res.fills), 1, "Should generate 1 fill on Bar 2")

        order = res.orders[0]
        fill = res.fills[0]

        # 1. Order was created at Bar 1 (t1)
        self.assertEqual(order.created_at, t1)

        # 2. Fill MUST execute at Bar 2 (t2), NOT Bar 1 (t1)
        self.assertEqual(fill.timestamp, t2, "Fill timestamp must equal Bar 2 (t2)")

        # 3. Temporal invariant assertion: fill.timestamp > order.created_at
        self.assertGreater(fill.timestamp, order.created_at, "Fill timestamp must be strictly greater than order creation time")

        # 4. Fill price must use Bar 2 Open price (201.0), NOT Bar 1 Open (100.0)
        self.assertNotEqual(fill.price, 100.0, "Fill price must not equal Bar 1 open (100.0)")
        self.assertAlmostEqual(fill.price, 201.0, places=2, msg="Fill price must use Bar 2 open (201.0)")

    def test_timing_short_order_execution(self):
        """[Spec Section 9]: Verify SHORT order generated at Bar T Close fills at Bar T+1 Open."""
        t0 = self.start_time
        t1 = self.start_time + timedelta(minutes=15)
        t2 = self.start_time + timedelta(minutes=30)

        data = [
            {"timestamp": t0, "open": 200.0, "high": 201.0, "low": 199.0, "close": 200.0, "volume": 10.0},
            {"timestamp": t1, "open": 200.0, "high": 201.0, "low": 99.0, "close": 100.0, "volume": 10.0},
            {"timestamp": t2, "open": 99.0, "high": 100.0, "low": 98.0, "close": 99.0, "volume": 10.0},
        ]
        df = pd.DataFrame(data)

        class BreakdownStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.price < 150.0:
                    return Signal(timestamp=context.timestamp, action=SignalAction.SHORT)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=BreakdownStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 1)
        self.assertEqual(len(res.fills), 1)

        fill = res.fills[0]
        self.assertEqual(fill.timestamp, t2)
        self.assertGreater(fill.timestamp, res.orders[0].created_at)
        self.assertAlmostEqual(fill.price, 99.0, places=2)

    def test_timing_reversal_order_execution(self):
        """[Spec Section 10]: Verify position reversal order generated at Bar T executes at Bar T+1."""
        t0 = self.start_time
        t1 = self.start_time + timedelta(minutes=15)
        t2 = self.start_time + timedelta(minutes=30)
        t3 = self.start_time + timedelta(minutes=45)

        data = [
            {"timestamp": t0, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0},
            {"timestamp": t1, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0}, # LONG signal
            {"timestamp": t2, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0}, # Fill LONG, SHORT signal
            {"timestamp": t3, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0}, # Fill Reversal SELL 2.0
        ]
        df = pd.DataFrame(data)

        class ReversalStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == t1:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                elif context.timestamp == t2:
                    return Signal(timestamp=context.timestamp, action=SignalAction.SHORT)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=ReversalStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 2)
        self.assertEqual(len(res.fills), 2)

        # Fill 1 for LONG order executes at t2
        self.assertEqual(res.fills[0].timestamp, t2)
        # Fill 2 for Reversal order (created at t2) executes at t3
        self.assertEqual(res.fills[1].timestamp, t3)
        self.assertEqual(res.fills[1].quantity, 2.0)

    def test_end_of_dataset_unfilled_order_behavior(self):
        """[Spec Section 6]: Order generated on final available bar (Bar N) remains unfilled."""
        t0 = self.start_time
        t1 = self.start_time + timedelta(minutes=15)

        data = [
            {"timestamp": t0, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0},
            {"timestamp": t1, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0}, # Final bar
        ]
        df = pd.DataFrame(data)

        class FinalBarStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == t1:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=FinalBarStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 1, "Should create 1 order on final bar")
        self.assertEqual(len(res.fills), 0, "Order on final bar must remain unfilled because no next bar exists")


if __name__ == "__main__":
    unittest.main()
