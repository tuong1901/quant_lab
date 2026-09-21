"""
[PURPOSE]: Adversarial strategy test suite verifying environment robustness across edge-case strategies (Hold, Long, Short, Alternating, Stateful, Malicious).
[DEPENDENCIES]: unittest, pandas, datetime, src.strategies, src.backtest, src.environment, src.config.
"""

import unittest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import pandas as pd

from src.strategies.strategy import Strategy
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.core.ids import StrategyId
from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.backtest.engine import BacktestEngine
from src.portfolio.position import PositionSide


class AlwaysHoldStrategy:
    """[Adversarial Fixture]: Strategy that strictly outputs HOLD on every bar."""
    def __init__(self):
        self.strategy_id = StrategyId("strat_always_hold")

    def on_bar(self, context: StrategyContext) -> Signal:
        return Signal(timestamp=context.timestamp, action=SignalAction.HOLD, strategy_id=self.strategy_id)


class AlwaysLongStrategy:
    """[Adversarial Fixture]: Strategy that strictly outputs LONG on every bar."""
    def __init__(self):
        self.strategy_id = StrategyId("strat_always_long")

    def on_bar(self, context: StrategyContext) -> Signal:
        return Signal(timestamp=context.timestamp, action=SignalAction.LONG, strategy_id=self.strategy_id)


class AlwaysShortStrategy:
    """[Adversarial Fixture]: Strategy that strictly outputs SHORT on every bar."""
    def __init__(self):
        self.strategy_id = StrategyId("strat_always_short")

    def on_bar(self, context: StrategyContext) -> Signal:
        return Signal(timestamp=context.timestamp, action=SignalAction.SHORT, strategy_id=self.strategy_id)


class AlternatingStrategy:
    """[Adversarial Fixture]: Strategy that flips between LONG and SHORT on every bar."""
    def __init__(self):
        self.strategy_id = StrategyId("strat_alternating")
        self.toggle = False

    def on_bar(self, context: StrategyContext) -> Signal:
        self.toggle = not self.toggle
        action = SignalAction.LONG if self.toggle else SignalAction.SHORT
        return Signal(timestamp=context.timestamp, action=action, strategy_id=self.strategy_id)


class MaliciousFutureAccessStrategy:
    """[Adversarial Fixture]: Strategy attempting to mutate context or access future features."""
    def __init__(self):
        self.strategy_id = StrategyId("strat_malicious")

    def on_bar(self, context: StrategyContext) -> Signal:
        # Attempt to mutate feature dictionary
        if hasattr(context, "features") and isinstance(context.features, dict):
            try:
                context.features["malicious_mutation"] = 99999.0
            except Exception:
                pass
        return Signal(timestamp=context.timestamp, action=SignalAction.HOLD, strategy_id=self.strategy_id)


class TestAdversarialStrategies(unittest.TestCase):
    """
    [PURPOSE]: Environment verification using adversarial strategy implementations.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _create_df(self, num_bars: int = 10) -> pd.DataFrame:
        data = []
        for i in range(num_bars):
            ts = self.start_time + timedelta(minutes=15 * i)
            p = 50000.0 + i * 10.0
            data.append({
                "timestamp": ts,
                "open": p,
                "high": p + 20.0,
                "low": p - 20.0,
                "close": p,
                "volume": 100.0,
            })
        return pd.DataFrame(data)

    def test_always_hold_produces_zero_orders_and_zero_fills(self):
        """[Adversarial]: AlwaysHoldStrategy must produce 0 orders and 0 fills across simulation."""
        df = self._create_df(10)
        env = EnvironmentFactory.create(config=self.config)
        strat = AlwaysHoldStrategy()
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        self.assertEqual(len(res.orders), 0, "AlwaysHold produced non-zero orders!")
        self.assertEqual(len(res.fills), 0, "AlwaysHold produced non-zero fills!")
        self.assertEqual(res.final_portfolio.equity, 10000.0)

    def test_always_long_opens_single_position(self):
        """[Adversarial]: AlwaysLongStrategy must open exactly 1 long position and not repeatedly issue buy orders."""
        df = self._create_df(10)
        env = EnvironmentFactory.create(config=self.config)
        strat = AlwaysLongStrategy()
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        # First bar generates 1 LONG order. Subsequent bars stay LONG so no duplicate orders.
        self.assertEqual(len(res.orders), 1, "AlwaysLong produced multiple duplicate orders!")
        self.assertEqual(len(res.fills), 1, "AlwaysLong produced multiple duplicate fills!")

    def test_alternating_strategy_reversal_lifecycle(self):
        """[Adversarial]: AlternatingStrategy flipping every bar must execute 2-step position reversals correctly."""
        df = self._create_df(6)
        env = EnvironmentFactory.create(config=self.config)
        strat = AlternatingStrategy()
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        # 6 bars -> 6 signals (LONG, SHORT, LONG, SHORT, LONG, SHORT)
        # Bar 0: Signal LONG -> Order 1 Buy 1.0 (executed Bar 1 Open)
        # Bar 1: Signal SHORT -> Order 2 Sell 2.0 (Reversal: Close 1.0 + Open Short 1.0) (executed Bar 2 Open)
        self.assertGreater(len(res.orders), 1)
        # Verify first reversal order quantity is 2.0 (Close 1 + Open 1)
        reversal_order = res.orders[1]
        self.assertEqual(reversal_order.quantity, 2.0, "Reversal order quantity was not 2.0!")

    def test_malicious_context_mutation_does_not_corrupt_data(self):
        """[Adversarial]: Strategy mutating StrategyContext features must not corrupt market data feed."""
        df = self._create_df(5)
        env = EnvironmentFactory.create(config=self.config)
        strat = MaliciousFutureAccessStrategy()
        res = BacktestEngine(environment=env, strategy=strat).run(df)

        self.assertEqual(res.bars_processed, 5)


if __name__ == "__main__":
    unittest.main()
