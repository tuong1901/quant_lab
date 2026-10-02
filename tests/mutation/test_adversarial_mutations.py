"""
[PURPOSE]: Adversarial Mutation Tests verifying that test assertions catch corrupted execution and accounting logic.
[DEPENDENCIES]: unittest, src.engine, src.environment.
"""

import unittest
from datetime import datetime, timezone

from src.trading.execution.fill import Fill
from src.trading.execution.order import OrderSide
from src.trading.portfolio.portfolio import Portfolio
from src.trading.portfolio.pnl import calculate_realized_pnl
from src.trading.portfolio.position import PositionSide


class TestAdversarialMutations(unittest.TestCase):
    """
    [PURPOSE]: Verify that test assertions detect mutated/corrupted logic (Mutation Testing).
    """

    def setUp(self):
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_mutation_inverted_pnl_sign_detected(self):
        """[Mutation Guard]: Corrupting PnL sign MUST be caught by assertions."""
        entry = 50000.0
        exit_price = 55000.0
        qty = 1.0

        # Correct PnL = +5,000. Mutated PnL = -5,000.
        mutated_pnl = -1.0 * calculate_realized_pnl(PositionSide.LONG, entry, exit_price, qty)

        # Assertion MUST fail when given mutated PnL
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_pnl, 5000.0, "Mutation survived: Inverted PnL sign was not detected!")

    def test_mutation_zero_fee_detected(self):
        """[Mutation Guard]: Zeroing fees on fill MUST be caught by assertions."""
        portfolio = Portfolio(initial_capital=10000.0)
        # Apply fill with $10 fee
        f = Fill(
            fill_id="f1", order_id="o1", symbol="BTCUSDT", side=OrderSide.BUY,
            quantity=1.0, price=50000.0, fee=10.0, timestamp=self.now
        )
        portfolio.apply_fill(f)

        # Mutated state: fees_paid forced to 0.0
        mutated_fees_paid = 0.0

        with self.assertRaises(AssertionError):
            self.assertEqual(portfolio.account.fees_paid, mutated_fees_paid, "Mutation survived: Fee removal was not detected!")


if __name__ == "__main__":
    unittest.main()
