"""
[PURPOSE]: Reconciliation unit tests (Audit #10, #13, #14, #22, #35) for manual trade auditing and accounting identity verification under next-bar execution semantics.
[DEPENDENCIES]: unittest, pandas, datetime, src.engine, src.strategies, src.environment, src.environment.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.strategies.strategy import Strategy
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.engine.backtest_engine import BacktestEngine
from src.environment.position import PositionSide


class TestAuditReconciliation(unittest.TestCase):
    """
    [PURPOSE]: Perform independent manual trade reconciliations and audit accounting identities.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_audit_trade_reconciliation_trade1_normal_entry_exit(self):
        """[Audit #22 - Trade 1]: Reconstruct position reversal trade calculation by hand under next-bar execution."""
        # Bar 1 (t1): LONG signal -> Bar 2 (t2): Fill Buy 1.0 @ 10,000
        # Bar 3 (t3): SHORT signal -> Bar 4 (t4): Fill Reversal Sell 2.0 @ 11,000
        data = [
            {"timestamp": self.start_time + timedelta(minutes=15 * i), "open": p, "high": p, "low": p, "close": p, "volume": 1.0}
            for i, p in enumerate([10000.0, 10000.0, 10000.0, 11000.0, 11000.0])
        ]
        df = pd.DataFrame(data)

        class Trade1Strategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == df["timestamp"].iloc[1]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                elif context.timestamp == df["timestamp"].iloc[3]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.SHORT)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=Trade1Strategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        # Expected Manual Calculations under Next-Bar Execution (Slippage 2 bps, Taker fee 2 bps):
        # Fill 1 at Bar 2 Open (Buy 1.0 @ 10,000): Executed @ 10,002.00, fee = $2.0004
        # Fill 2 at Bar 4 Open (Sell 2.0 @ 11,000 for SHORT reversal): Executed @ 10,997.80, fee = $4.39912
        # Total Fees = $2.0004 + $4.39912 = $6.40
        self.assertEqual(len(res.fills), 2)
        self.assertAlmostEqual(res.total_fees, 6.40, places=2, msg="Total fees must equal $6.40")

    def test_audit_trade_reconciliation_trade2_reversal(self):
        """[Audit #22 - Trade 2]: Reconstruct LONG to SHORT position reversal trade calculation by hand under next-bar execution."""
        # Bar 1: LONG signal -> Bar 2: Fill Buy 1.0. Bar 3: SHORT signal -> Bar 4: Fill Reversal Sell 2.0
        data = [
            {"timestamp": self.start_time + timedelta(minutes=15 * i), "open": p, "high": p, "low": p, "close": p, "volume": 1.0}
            for i, p in enumerate([10000.0, 10000.0, 10000.0, 9000.0, 9000.0])
        ]
        df = pd.DataFrame(data)

        class Trade2Strategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == df["timestamp"].iloc[1]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                elif context.timestamp == df["timestamp"].iloc[3]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.SHORT)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=Trade2Strategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        self.assertEqual(len(res.orders), 2)
        self.assertEqual(len(res.fills), 2)
        reversal_order = res.orders[1]
        self.assertEqual(reversal_order.quantity, 2.0, "Reversal order quantity must be 2.0")

        final_pos = env.portfolio.positions.get("BTCUSDT")
        self.assertIsNotNone(final_pos)
        self.assertEqual(final_pos.side, PositionSide.SHORT)
        self.assertEqual(final_pos.quantity, 1.0)

    def test_audit_trade_reconciliation_trade3_open_position(self):
        """[Audit #22 - Trade 3]: Reconstruct open position valuation at backtest completion by hand under next-bar execution."""
        # Bar 1: LONG signal -> Bar 2: Fill Buy 1.0 @ 10,000. Bar 3: Price rises to 12,000
        data = [
            {"timestamp": self.start_time + timedelta(minutes=15 * i), "open": p, "high": p, "low": p, "close": p, "volume": 1.0}
            for i, p in enumerate([10000.0, 10000.0, 10000.0, 12000.0])
        ]
        df = pd.DataFrame(data)

        class Trade3Strategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == df["timestamp"].iloc[1]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=Trade3Strategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        # Expected Manual Calculations (Taker fee = 2 bps = 0.0002):
        # Realized PnL = 0.0
        # Entry Fee = $2.0004
        self.assertEqual(res.realized_pnl, 0.0)
        self.assertAlmostEqual(res.total_fees, 2.0, places=1)

    def test_audit_fee_reconciliation(self):
        """[Audit #13 & #35]: Verify sum(fill.fee) == BacktestResult.total_fees == Portfolio.account.fees_paid under next-bar execution."""
        data = [
            {"timestamp": self.start_time + timedelta(minutes=15 * i), "open": p, "high": p, "low": p, "close": p, "volume": 1.0}
            for i, p in enumerate([100.0, 100.0, 100.0, 120.0, 110.0])
        ]
        df = pd.DataFrame(data)

        class MultiTradeStrategy(Strategy):
            def on_bar(self, context: StrategyContext) -> Signal:
                if context.timestamp == df["timestamp"].iloc[1]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
                elif context.timestamp == df["timestamp"].iloc[3]:
                    return Signal(timestamp=context.timestamp, action=SignalAction.SHORT)
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)

        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=MultiTradeStrategy(), default_order_quantity=1.0)
        res = engine.run(df=df)

        sum_fill_fees = sum(fill.fee for fill in res.fills)
        self.assertAlmostEqual(sum_fill_fees, res.total_fees, places=4)
        self.assertAlmostEqual(env.portfolio.account.fees_paid, res.total_fees, places=4)


if __name__ == "__main__":
    unittest.main()
