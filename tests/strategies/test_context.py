"""
Unit tests for StrategyContext read-only container (`src/strategies/context.py`).
"""

import unittest
from datetime import datetime, timezone

from src.portfolio.position import PositionSide


class TestStrategyContext(unittest.TestCase):
    """
    [PURPOSE]: Verify StrategyContext narrow read-only container.
    """

    def test_context_creation_and_immutability(self):
        """Test creating StrategyContext with timestamp, price, position_side, and features."""
        from src.strategies.context import StrategyContext

        now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        ctx = StrategyContext(
            timestamp=now,
            price=50000.0,
            position_side=PositionSide.LONG,
            features={"ema20": 50100.0, "ema50": 49800.0},
        )

        self.assertEqual(ctx.timestamp, now)
        self.assertEqual(ctx.price, 50000.0)
        self.assertEqual(ctx.position_side, PositionSide.LONG)
        self.assertEqual(ctx.features["ema20"], 50100.0)

        with self.assertRaises(AttributeError):
            ctx.price = 50200.0


if __name__ == "__main__":
    unittest.main()
