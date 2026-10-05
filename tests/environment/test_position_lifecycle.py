"""
[PURPOSE]: Unit tests for 5 Position lifecycle transitions (Open, Increase, Reduce, Close, Reversal).
[DEPENDENCIES]: unittest, datetime, src.engine, src.environment.
"""

import unittest
from datetime import datetime, timezone
from src.trading import Fill, OrderSide
from src.trading import Portfolio, Position, PositionSide, InvalidPositionError

class TestPositionLifecycle(unittest.TestCase):
    def test_open_and_increase_position_weighted_average(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=100000.0)

        # 6.1 Open Long: BUY 1 BTC @ 60,000
        f1 = Fill("fill_1", "ord_1", "BTCUSDT", OrderSide.BUY, quantity=1.0, price=60000.0, timestamp=ts)
        state1 = portfolio.apply_fill(f1)

        pos1 = portfolio.get_position("BTCUSDT")
        self.assertIsNotNone(pos1)
        self.assertEqual(pos1.side, PositionSide.LONG)
        self.assertEqual(pos1.quantity, 1.0)
        self.assertEqual(pos1.average_entry_price, 60000.0)

        # 6.2 Increase Long: BUY 1 BTC @ 62,000
        f2 = Fill("fill_2", "ord_2", "BTCUSDT", OrderSide.BUY, quantity=1.0, price=62000.0, timestamp=ts)
        portfolio.apply_fill(f2)

        pos2 = portfolio.get_position("BTCUSDT")
        self.assertEqual(pos2.quantity, 2.0)
        # Weighted average = (1 * 60000 + 1 * 62000) / 2 = 61000
        self.assertEqual(pos2.average_entry_price, 61000.0)

    def test_reduce_and_close_position(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=100000.0)

        # Setup LONG 2 BTC @ 61,000
        portfolio.apply_fill(Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 60000.0, ts))
        portfolio.apply_fill(Fill("f2", "o2", "BTCUSDT", OrderSide.BUY, 1.0, 62000.0, ts))

        # 7. Reduce: SELL 0.5 BTC @ 63,000 -> Realized PnL = (63000 - 61000) * 0.5 = +1000
        f3 = Fill("f3", "o3", "BTCUSDT", OrderSide.SELL, quantity=0.5, price=63000.0, timestamp=ts)
        portfolio.apply_fill(f3)

        pos3 = portfolio.get_position("BTCUSDT")
        self.assertEqual(pos3.quantity, 1.5)
        self.assertEqual(pos3.average_entry_price, 61000.0)  # Entry unchanged on reduction!
        self.assertEqual(portfolio.account.realized_pnl, 1000.0)

        # 8. Close Remaining 1.5 BTC @ 63,000 -> Realized PnL = (63000 - 61000) * 1.5 = +3000
        f4 = Fill("f4", "o4", "BTCUSDT", OrderSide.SELL, quantity=1.5, price=63000.0, timestamp=ts)
        portfolio.apply_fill(f4)

        pos4 = portfolio.get_position("BTCUSDT")
        self.assertIsNone(pos4)  # Position flat!
        self.assertEqual(portfolio.account.realized_pnl, 4000.0)  # Total 1000 + 3000

    def test_position_reversal_long_to_short(self):
        """
        [SPECIFICATION SECTION 9]: Reversal Long -> Short
        LONG 1 BTC @ 60,000.
        Fill: SELL 2 BTC @ 63,000.
        Expected: Step 1 Close LONG 1 BTC (PnL +3000), Step 2 Open SHORT 1 BTC @ 63,000.
        """
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=100000.0)

        # Open Long 1 BTC @ 60,000
        portfolio.apply_fill(Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 60000.0, ts))

        # Reversal Sell 2 BTC @ 63,000
        portfolio.apply_fill(Fill("f2", "o2", "BTCUSDT", OrderSide.SELL, 2.0, 63000.0, ts))

        pos = portfolio.get_position("BTCUSDT")
        self.assertIsNotNone(pos)
        self.assertEqual(pos.side, PositionSide.SHORT)
        self.assertEqual(pos.quantity, 1.0)
        self.assertEqual(pos.average_entry_price, 63000.0)
        self.assertEqual(portfolio.account.realized_pnl, 3000.0)

    def test_position_invariants(self):
        # Position quantity must be > 0 (Never -1 for Short)
        with self.assertRaises(InvalidPositionError):
            Position("BTCUSDT", PositionSide.SHORT, quantity=-1.0, average_entry_price=60000.0)

if __name__ == "__main__":
    unittest.main()
