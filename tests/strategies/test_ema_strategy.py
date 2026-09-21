"""
Unit tests for EMAStrategy reference implementation (`src/strategies/ema.py`).
"""

import unittest
from datetime import datetime, timezone

from src.portfolio.position import PositionSide


class TestEMAStrategy(unittest.TestCase):
    """
    [PURPOSE]: Verify EMAStrategy signal logic (EMA20 > EMA50 -> LONG, EMA20 < EMA50 -> SHORT, EMA20 == EMA50 -> HOLD).
    """

    def setUp(self):
        self.now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    def test_ema_cross_long(self):
        """Test EMA20 > EMA50 returns LONG signal."""
        from src.strategies.ema import EMAStrategy
        from src.strategies.context import StrategyContext
        from src.strategies.signal import SignalAction

        strat = EMAStrategy(fast_period=20, slow_period=50)
        ctx = StrategyContext(
            timestamp=self.now,
            price=50000.0,
            position_side=None,
            features={"ema20": 50500.0, "ema50": 50000.0},
        )

        sig = strat.on_bar(ctx)
        self.assertEqual(sig.action, SignalAction.LONG)

    def test_ema_cross_short(self):
        """Test EMA20 < EMA50 returns SHORT signal."""
        from src.strategies.ema import EMAStrategy
        from src.strategies.context import StrategyContext
        from src.strategies.signal import SignalAction

        strat = EMAStrategy(fast_period=20, slow_period=50)
        ctx = StrategyContext(
            timestamp=self.now,
            price=50000.0,
            position_side=PositionSide.LONG,
            features={"ema20": 49500.0, "ema50": 50000.0},
        )

        sig = strat.on_bar(ctx)
        self.assertEqual(sig.action, SignalAction.SHORT)

    def test_ema_equal_hold(self):
        """Test EMA20 == EMA50 returns HOLD signal."""
        from src.strategies.ema import EMAStrategy
        from src.strategies.context import StrategyContext
        from src.strategies.signal import SignalAction

        strat = EMAStrategy(fast_period=20, slow_period=50)
        ctx = StrategyContext(
            timestamp=self.now,
            price=50000.0,
            position_side=None,
            features={"ema20": 50000.0, "ema50": 50000.0},
        )

        sig = strat.on_bar(ctx)
        self.assertEqual(sig.action, SignalAction.HOLD)

    def test_missing_features_fallback_hold(self):
        """Test that missing EMA feature keys fall back to HOLD without raising error."""
        from src.strategies.ema import EMAStrategy
        from src.strategies.context import StrategyContext
        from src.strategies.signal import SignalAction

        strat = EMAStrategy(fast_period=20, slow_period=50)
        ctx = StrategyContext(
            timestamp=self.now,
            price=50000.0,
            position_side=None,
            features={},
        )

        sig = strat.on_bar(ctx)
        self.assertEqual(sig.action, SignalAction.HOLD)


if __name__ == "__main__":
    unittest.main()
