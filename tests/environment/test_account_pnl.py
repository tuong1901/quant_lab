"""
[PURPOSE]: Unit tests for Account and PnL mathematical formulas.
[DEPENDENCIES]: unittest, src.environment.
"""

import unittest
from src.environment import (
    Account,
    PositionSide,
    calculate_unrealized_pnl,
    calculate_realized_pnl,
    PortfolioException,
)

class TestAccountAndPnL(unittest.TestCase):
    def test_account_initialization_and_equity(self):
        acc = Account(initial_capital=10000.0, balance=10000.0)
        self.assertEqual(acc.compute_equity(total_unrealized_pnl=500.0), 10500.0)
        self.assertEqual(acc.compute_equity(total_unrealized_pnl=-200.0), 9800.0)

        with self.assertRaises(PortfolioException):
            Account(initial_capital=0.0, balance=0.0)

    def test_account_apply_transaction(self):
        acc = Account(initial_capital=10000.0, balance=10000.0)
        # Apply trade: realized_pnl = +1000, fee = 10
        updated = acc.apply_transaction(realized_pnl_delta=1000.0, fee_delta=10.0)

        self.assertEqual(updated.balance, 10990.0)  # 10000 + 1000 - 10
        self.assertEqual(updated.realized_pnl, 1000.0)
        self.assertEqual(updated.fees_paid, 10.0)
        self.assertEqual(updated.compute_equity(0.0), 10990.0)

    def test_pnl_formulas_long(self):
        # Long Entry=60,000, Mark=63,000, Qty=2 -> Unrealized = (63000 - 60000) * 2 = 6,000
        unrealized = calculate_unrealized_pnl(PositionSide.LONG, entry_price=60000.0, mark_price=63000.0, quantity=2.0)
        self.assertEqual(unrealized, 6000.0)

        # Realized PnL Long: Entry=60,000, Exit=63,000, Closed Qty=1.5 -> +4,500
        realized = calculate_realized_pnl(PositionSide.LONG, entry_price=60000.0, exit_price=63000.0, closed_quantity=1.5)
        self.assertEqual(realized, 4500.0)

    def test_pnl_formulas_short(self):
        # Short Entry=63,000, Mark=60,000, Qty=2 -> Unrealized = (63000 - 60000) * 2 = 6,000
        unrealized = calculate_unrealized_pnl(PositionSide.SHORT, entry_price=63000.0, mark_price=60000.0, quantity=2.0)
        self.assertEqual(unrealized, 6000.0)

        # Realized PnL Short: Entry=63,000, Exit=60,000, Closed Qty=1.0 -> +3,000
        realized = calculate_realized_pnl(PositionSide.SHORT, entry_price=63000.0, exit_price=60000.0, closed_quantity=1.0)
        self.assertEqual(realized, 3000.0)

if __name__ == "__main__":
    unittest.main()
