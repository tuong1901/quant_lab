"""
[PURPOSE]: Synthetic scenario unit tests (Scenarios A through F) for forensic backtest integrity audit.
[DEPENDENCIES]: unittest, pandas, datetime, src.backtest, src.strategies, src.environment, src.evaluation.
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
from src.evaluation.metrics import calculate_basic_metrics
from src.portfolio.position import PositionSide


class ScriptedStrategy(Strategy):
    """
    [PURPOSE]: A deterministic strategy that emits predefined signals at specific bar indices.
    """
    def __init__(self, action_map: dict):
        self.action_map = action_map  # bar_index -> SignalAction
        self.bar_index = 0

    def on_bar(self, context: StrategyContext) -> Signal:
        action = self.action_map.get(self.bar_index, SignalAction.HOLD)
        self.bar_index += 1
        return Signal(timestamp=context.timestamp, action=action, strategy_id="scripted")


class TestAuditScenarios(unittest.TestCase):
    """
    [PURPOSE]: Verify fundamental trading scenarios A through F against expected hand calculations.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _create_synthetic_df(self, prices: list) -> pd.DataFrame:
        data = []
        for i, p in enumerate(prices):
            ts = self.start_time + timedelta(minutes=15 * i)
            data.append({
                "timestamp": ts,
                "open": p,
                "high": p + 1.0,
                "low": p - 1.0,
                "close": p,
                "volume": 10.0
            })
        return pd.DataFrame(data)

    def test_scenario_a_long_profit(self):
        """Scenario A: FLAT -> LONG -> price rises -> CLOSE -> Net Profit under next-bar execution."""
        # Bar 1 (price 100): LONG signal -> Bar 2 (price 100): Buy 1.0 @ 100.0
        # Bar 3 (price 110): SHORT signal -> Bar 4 (price 120): Sell 1.0 @ 120.0
        df = self._create_synthetic_df([100.0, 100.0, 100.0, 110.0, 120.0])
        strat = ScriptedStrategy({1: SignalAction.LONG, 3: SignalAction.SHORT})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertGreater(metrics.realized_pnl, 0.0, "LONG profit scenario should produce positive realized PnL")
        self.assertGreater(metrics.final_equity, metrics.initial_capital, "Final equity should exceed initial capital")

    def test_scenario_b_long_loss(self):
        """Scenario B: FLAT -> LONG -> price falls -> CLOSE -> Net Loss under next-bar execution."""
        # Bar 1 (price 100): LONG signal -> Bar 2 (price 100): Buy 1.0 @ 100.0
        # Bar 3 (price 90): SHORT signal -> Bar 4 (price 80): Sell 1.0 @ 80.0
        df = self._create_synthetic_df([100.0, 100.0, 100.0, 90.0, 80.0])
        strat = ScriptedStrategy({1: SignalAction.LONG, 3: SignalAction.SHORT})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertLess(metrics.realized_pnl, 0.0, "LONG loss scenario should produce negative realized PnL")
        self.assertLess(metrics.final_equity, metrics.initial_capital, "Final equity should be less than initial capital")

    def test_scenario_c_short_profit(self):
        """Scenario C: FLAT -> SHORT -> price falls -> CLOSE -> Net Profit under next-bar execution."""
        # Bar 1 (price 100): SHORT signal -> Bar 2 (price 100): Sell 1.0 @ 100.0
        # Bar 3 (price 90): LONG signal -> Bar 4 (price 80): Buy 1.0 @ 80.0
        df = self._create_synthetic_df([100.0, 100.0, 100.0, 90.0, 80.0])
        strat = ScriptedStrategy({1: SignalAction.SHORT, 3: SignalAction.LONG})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertGreater(metrics.realized_pnl, 0.0, "SHORT profit scenario should produce positive realized PnL")
        self.assertGreater(metrics.final_equity, metrics.initial_capital, "Final equity should exceed initial capital")

    def test_scenario_d_short_loss(self):
        """Scenario D: FLAT -> SHORT -> price rises -> CLOSE -> Net Loss under next-bar execution."""
        # Bar 1 (price 100): SHORT signal -> Bar 2 (price 100): Sell 1.0 @ 100.0
        # Bar 3 (price 110): LONG signal -> Bar 4 (price 120): Buy 1.0 @ 120.0
        df = self._create_synthetic_df([100.0, 100.0, 100.0, 110.0, 120.0])
        strat = ScriptedStrategy({1: SignalAction.SHORT, 3: SignalAction.LONG})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertLess(metrics.realized_pnl, 0.0, "SHORT loss scenario should produce negative realized PnL")
        self.assertLess(metrics.final_equity, metrics.initial_capital, "Final equity should be less than initial capital")

    def test_scenario_e_reversal(self):
        """Scenario E: Reversal LONG -> SHORT under next-bar execution."""
        # Bar 1: LONG signal -> Bar 2: Fill LONG 1.0. Bar 3: SHORT signal -> Bar 4: Fill Reversal SELL 2.0
        df = self._create_synthetic_df([100.0, 100.0, 105.0, 105.0, 105.0])
        strat = ScriptedStrategy({1: SignalAction.LONG, 3: SignalAction.SHORT})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        # Check final active position is SHORT
        final_pos = env.portfolio.positions.get("BTCUSDT")
        self.assertIsNotNone(final_pos)
        self.assertEqual(final_pos.side, PositionSide.SHORT)
        self.assertEqual(final_pos.quantity, 1.0)

    def test_scenario_f_open_position_end(self):
        """Scenario F: Open position remaining at backtest end under next-bar execution."""
        # Bar 1: LONG signal -> Bar 2: Fill LONG 1.0. Bar 3, 4: Price rises to 120, 130
        df = self._create_synthetic_df([100.0, 100.0, 110.0, 120.0, 130.0])
        strat = ScriptedStrategy({1: SignalAction.LONG})
        env = EnvironmentFactory.create(config=self.config)
        engine = BacktestEngine(environment=env, strategy=strat, default_order_quantity=1.0)
        res = engine.run(df=df)

        metrics = calculate_basic_metrics(res)
        self.assertEqual(metrics.realized_pnl, 0.0, "Unclosed position should have 0 realized PnL")
        self.assertGreater(metrics.net_pnl, 0.0, "Net PnL should reflect unrealized profit in equity")
        self.assertEqual(metrics.final_equity, metrics.initial_capital + metrics.net_pnl)


if __name__ == "__main__":
    unittest.main()
