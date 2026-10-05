"""
Unit tests for Strategy Protocol contract and isolation constraints (`src/strategies/strategy.py`).
"""

import unittest
from datetime import datetime, timezone

from src.trading.portfolio.position import PositionSide


class TestStrategyContract(unittest.TestCase):
    """
    [PURPOSE]: Verify Strategy Protocol interface and non-mutation behavior.
    """

    def test_protocol_isinstance_check(self):
        """Test that objects implementing Strategy Protocol satisfy isinstance check."""
        from src.strategies.strategy import Strategy
        from src.strategies.context import StrategyContext
        from src.strategies.signal import Signal, SignalAction

        class DummyStrategy:
            @property
            def strategy_id(self) -> str:
                return "dummy_01"

            def on_bar(self, context: StrategyContext) -> Signal:
                return Signal(timestamp=context.timestamp, action=SignalAction.HOLD, strategy_id=self.strategy_id)

        dummy = DummyStrategy()
        self.assertTrue(isinstance(dummy, Strategy))

    def test_strategy_evaluation_has_no_side_effects(self):
        """Test that strategy on_bar evaluation does not mutate StrategyContext or external parameters."""
        from src.strategies.context import StrategyContext
        from src.strategies.signal import Signal, SignalAction

        class SimpleTestStrategy:
            @property
            def strategy_id(self) -> str:
                return "simple_test"

            def on_bar(self, context: StrategyContext) -> Signal:
                # Read features without mutation
                action = SignalAction.LONG if context.price > 100.0 else SignalAction.SHORT
                return Signal(timestamp=context.timestamp, action=action, strategy_id=self.strategy_id)

        strat = SimpleTestStrategy()
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ctx = StrategyContext(timestamp=now, price=150.0, position_side=None, features={"indicator": 1.0})

        sig = strat.on_bar(ctx)

        # Confirm expected output and no mutation of context
        self.assertEqual(sig.action, SignalAction.LONG)
        self.assertEqual(ctx.price, 150.0)
        self.assertEqual(ctx.features["indicator"], 1.0)


if __name__ == "__main__":
    unittest.main()
