"""
[PURPOSE]: Invariant tests verifying fundamental accounting formulas across 8 hand-derived trade lifecycle transitions.
[DEPENDENCIES]: unittest, datetime, src.environment, src.engine.
"""

import unittest
from datetime import datetime, timezone

from src.trading.portfolio.portfolio import Portfolio
from src.trading.portfolio.position import PositionSide
from src.trading.execution.fill import Fill
from src.trading.execution.order import OrderSide


class TestAccountingInvariants(unittest.TestCase):
    """
    [PURPOSE]: Verify mathematical accounting invariants: Equity = Balance + Unrealized PnL, Cash = Initial + Realized - Fees - Funding.
    """

    def setUp(self):
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.portfolio = Portfolio(initial_capital=10000.0)

    def _assert_accounting_equation(self, symbol: str, mark_price: float):
        p_state = self.portfolio.mark_to_market(self.now, {symbol: mark_price})
        expected_cash = (
            10000.0
            + self.portfolio.account.realized_pnl
            - self.portfolio.account.fees_paid
            - self.portfolio.account.funding_paid
        )
        self.assertAlmostEqual(self.portfolio.account.balance, expected_cash, places=6, msg="Cash balance invariant breached!")
        self.assertAlmostEqual(p_state.equity, p_state.balance + p_state.unrealized_pnl, places=6, msg="Equity equation invariant breached!")

    def test_scenario_flat_to_long_to_flat(self):
        """[Accounting Invariant]: Scenario FLAT -> LONG -> FLAT hand-calculated reconciliation."""
        # 1. FLAT -> LONG (Buy 1 BTC at $50,000, Fee $10)
        f1 = Fill(
            fill_id="f1", order_id="o1", symbol="BTCUSDT", side=OrderSide.BUY,
            quantity=1.0, price=50000.0, fee=10.0, timestamp=self.now
        )
        self.portfolio.apply_fill(f1)
        self._assert_accounting_equation("BTCUSDT", 52000.0)

        # 2. LONG -> FLAT (Sell 1 BTC at $55,000, Fee $11)
        # Expected Realized PnL = ($55,000 - $50,000) * 1.0 = +$5,000.
        # Total Fees = $10 + $11 = $21.
        # Final Cash = $10,000 + $5,000 - $21 = $14,979.
        f2 = Fill(
            fill_id="f2", order_id="o2", symbol="BTCUSDT", side=OrderSide.SELL,
            quantity=1.0, price=55000.0, fee=11.0, timestamp=self.now
        )
        self.portfolio.apply_fill(f2)
        
        self.assertAlmostEqual(self.portfolio.account.realized_pnl, 5000.0, places=6)
        self.assertAlmostEqual(self.portfolio.account.fees_paid, 21.0, places=6)
        self.assertAlmostEqual(self.portfolio.account.balance, 14979.0, places=6)
        self._assert_accounting_equation("BTCUSDT", 55000.0)

    def test_scenario_flat_to_short_to_reversal(self):
        """[Accounting Invariant]: Scenario FLAT -> SHORT -> REVERSAL LONG hand-calculated reconciliation."""
        # 1. FLAT -> SHORT (Sell 1 BTC at $50,000, Fee $10)
        f1 = Fill(
            fill_id="f1", order_id="o1", symbol="BTCUSDT", side=OrderSide.SELL,
            quantity=1.0, price=50000.0, fee=10.0, timestamp=self.now
        )
        self.portfolio.apply_fill(f1)
        self._assert_accounting_equation("BTCUSDT", 48000.0)

        # 2. SHORT -> REVERSAL LONG (Buy 2 BTC at $45,000, Fee $18)
        # Close SHORT 1.0 @ 45,000 -> Realized PnL = (50,000 - 45,000) * 1.0 = +$5,000.
        # Open LONG 1.0 @ 45,000.
        # Total Fees = $10 + $18 = $28.
        # Balance = $10,000 + $5,000 - $28 = $14,972.
        f2 = Fill(
            fill_id="f2", order_id="o2", symbol="BTCUSDT", side=OrderSide.BUY,
            quantity=2.0, price=45000.0, fee=18.0, timestamp=self.now
        )
        self.portfolio.apply_fill(f2)

        self.assertAlmostEqual(self.portfolio.account.realized_pnl, 5000.0, places=6)
        self.assertAlmostEqual(self.portfolio.account.balance, 14972.0, places=6)
        self.assertEqual(self.portfolio.positions["BTCUSDT"].side, PositionSide.LONG)
        self.assertEqual(self.portfolio.positions["BTCUSDT"].quantity, 1.0)
        self._assert_accounting_equation("BTCUSDT", 47000.0)


if __name__ == "__main__":
    unittest.main()
