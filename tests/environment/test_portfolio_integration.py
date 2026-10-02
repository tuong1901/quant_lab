"""
[PURPOSE]: Unit tests for Portfolio integration end-to-end (apply_fill, mark_to_market, duplicate fill protection, multi-symbol, determinism).
[DEPENDENCIES]: unittest, datetime, src.engine, src.environment.
"""

import unittest
from datetime import datetime, timezone
from src.engine import Fill, OrderSide
from src.environment import Portfolio, PositionSide

class TestPortfolioIntegration(unittest.TestCase):
    def test_portfolio_end_to_end_example(self):
        """
        [SPECIFICATION SECTION 30]: End-to-End Execution Scenario
        Initial Capital = 10,000 USD, Leverage = 5x
        Fill: BUY 0.5 BTC @ 60,010, Fee = 12.002
        Mark Price = 61,000 -> Unrealized PnL = (61000 - 60010) * 0.5 = +495
        Fill: SELL 0.5 BTC @ 61,000, Fee = 12.20
        """
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=10000.0, leverage=5.0)

        # Apply BUY fill
        f1 = Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, quantity=0.5, price=60010.0, timestamp=ts, fee=12.002)
        state1 = portfolio.apply_fill(f1)

        pos1 = portfolio.get_position("BTCUSDT")
        self.assertIsNotNone(pos1)
        self.assertEqual(pos1.side, PositionSide.LONG)
        self.assertEqual(pos1.quantity, 0.5)
        self.assertEqual(pos1.average_entry_price, 60010.0)

        # Mark to market @ 61,000
        state2 = portfolio.mark_to_market("BTCUSDT", mark_price=61000.0, timestamp=ts)
        self.assertEqual(state2.unrealized_pnl, 495.0)
        self.assertEqual(state2.balance, 9987.998) # 10000 - 12.002
        self.assertEqual(state2.equity, 9987.998 + 495.0) # 10482.998

        # Used margin = notional / 5 = (0.5 * 60010) / 5 = 30005 / 5 = 6001.0
        self.assertAlmostEqual(state2.used_margin, 6001.0, places=2)

        # Apply SELL fill @ 61,000
        f2 = Fill("f2", "o2", "BTCUSDT", OrderSide.SELL, quantity=0.5, price=61000.0, timestamp=ts, fee=12.2)
        state3 = portfolio.apply_fill(f2)

        self.assertIsNone(portfolio.get_position("BTCUSDT")) # Flat!
        self.assertEqual(state3.realized_pnl, 495.0)
        self.assertAlmostEqual(state3.fees_paid, 24.202, places=4) # 12.002 + 12.2
        # Net balance = 10000 + 495 - 24.202 = 10470.798
        self.assertAlmostEqual(state3.balance, 10470.798, places=3)
        self.assertAlmostEqual(state3.equity, 10470.798, places=3)

    def test_duplicate_fill_prevention(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=10000.0)
        f1 = Fill("dup_f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 50000.0, ts, fee=5.0)

        portfolio.apply_fill(f1)
        self.assertEqual(portfolio.account.balance, 9995.0)

        # Apply same fill again -> Duplicate check prevents double accounting!
        portfolio.apply_fill(f1)
        self.assertEqual(portfolio.account.balance, 9995.0)

    def test_multi_symbol_portfolio(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=50000.0)

        portfolio.apply_fill(Fill("f_btc", "o_btc", "BTCUSDT", OrderSide.BUY, 1.0, 60000.0, ts))
        portfolio.apply_fill(Fill("f_eth", "o_eth", "ETHUSDT", OrderSide.BUY, 10.0, 3000.0, ts))

        self.assertIsNotNone(portfolio.get_position("BTCUSDT"))
        self.assertIsNotNone(portfolio.get_position("ETHUSDT"))
        self.assertEqual(len(portfolio.positions), 2)

    def test_portfolio_determinism(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        fills = [
            Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 60000.0, ts, fee=10.0),
            Fill("f2", "o2", "BTCUSDT", OrderSide.BUY, 1.0, 62000.0, ts, fee=10.0),
            Fill("f3", "o3", "BTCUSDT", OrderSide.SELL, 2.0, 65000.0, ts, fee=20.0),
        ]

        def run_sim():
            p = Portfolio(initial_capital=50000.0)
            states = []
            for f in fills:
                states.append(p.apply_fill(f))
            return states

        states1 = run_sim()
        states2 = run_sim()
        self.assertEqual(states1, states2)

if __name__ == "__main__":
    unittest.main()
