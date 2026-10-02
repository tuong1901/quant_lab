"""
[PURPOSE]: Property-based tests verifying monotonic PnL behaviors and non-negativity range properties.
[DEPENDENCIES]: unittest, src.environment.accounting.pnl.
"""

import unittest

from src.environment.accounting.pnl import calculate_realized_pnl
from src.environment.accounting.position import PositionSide


class TestRangeProperties(unittest.TestCase):
    """
    [PURPOSE]: Range and monotonicity property tests.
    """

    def test_long_pnl_monotonic_increase_with_higher_exit(self):
        """[Property]: For LONG positions, increasing exit price must strictly increase gross PnL."""
        entry_price = 50000.0
        qty = 1.0

        pnl_low = calculate_realized_pnl(PositionSide.LONG, entry_price, 51000.0, qty)
        pnl_mid = calculate_realized_pnl(PositionSide.LONG, entry_price, 52000.0, qty)
        pnl_high = calculate_realized_pnl(PositionSide.LONG, entry_price, 53000.0, qty)

        self.assertLess(pnl_low, pnl_mid)
        self.assertLess(pnl_mid, pnl_high)

    def test_short_pnl_monotonic_increase_with_lower_exit(self):
        """[Property]: For SHORT positions, decreasing exit price must strictly increase gross PnL."""
        entry_price = 50000.0
        qty = 1.0

        pnl_worst = calculate_realized_pnl(PositionSide.SHORT, entry_price, 49000.0, qty)
        pnl_better = calculate_realized_pnl(PositionSide.SHORT, entry_price, 48000.0, qty)
        pnl_best = calculate_realized_pnl(PositionSide.SHORT, entry_price, 47000.0, qty)

        self.assertLess(pnl_worst, pnl_better)
        self.assertLess(pnl_better, pnl_best)

    def test_zero_quantity_produces_zero_pnl(self):
        """[Property]: Zero quantity MUST produce 0 PnL."""
        pnl = calculate_realized_pnl(PositionSide.LONG, 50000.0, 60000.0, 0.0)
        self.assertEqual(pnl, 0.0)


if __name__ == "__main__":
    unittest.main()
