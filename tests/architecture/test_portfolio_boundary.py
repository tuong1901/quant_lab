"""
[PURPOSE]: Portfolio Boundary Guard tests ensuring Portfolio subsystem updates state strictly via Fill operations and MTM without calling Strategy or Execution.
[DEPENDENCIES]: unittest, ast, pathlib, src.environment.
"""

import ast
from pathlib import Path
import unittest

from src.environment.accounting.portfolio import Portfolio
from src.engine.execution.fill import Fill
from src.engine.execution.order import OrderSide
from datetime import datetime, timezone


class TestPortfolioBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Portfolio subsystem boundary invariants.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.portfolio_dir = self.project_root / "src" / "portfolio"
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_portfolio_ast_forbidden_references(self):
        """[Portfolio Boundary]: Portfolio modules must not import Strategy or Backtest Engine."""
        forbidden_imports = {
            "src.strategies",
            "src.engine",
        }
        violations = []

        for file in self.portfolio_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in forbidden_imports:
                        if node.module == forbidden or node.module.startswith(forbidden + "."):
                            violations.append(f"{file.name} imports forbidden module '{node.module}'")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_imports:
                            if alias.name == forbidden or alias.name.startswith(forbidden + "."):
                                violations.append(f"{file.name} imports forbidden module '{alias.name}'")

        if violations:
            self.fail("Portfolio Boundary Violation:\n" + "\n".join(violations))

    def test_portfolio_updates_state_via_fill_only(self):
        """[Portfolio Boundary]: Portfolio state updates strictly via apply_fill and mark_to_market."""
        portfolio = Portfolio(initial_capital=10000.0)

        self.assertEqual(portfolio.initial_capital, 10000.0)
        self.assertEqual(portfolio.account.balance, 10000.0)
        self.assertEqual(len(portfolio.positions), 0)

        fill = Fill(
            fill_id="fill_port_boundary",
            order_id="ord_port_boundary",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            fee=10.0,
            timestamp=self.now,
        )

        p_state_fill = portfolio.apply_fill(fill)

        # Cash balance debited only fee
        self.assertEqual(portfolio.account.balance, 9990.0)
        self.assertEqual(portfolio.account.fees_paid, 10.0)
        self.assertEqual(p_state_fill.equity, 9990.0)
        self.assertIn("BTCUSDT", portfolio.positions)

        # Mark to market at 51,000 (+1,000 unrealized PnL)
        p_state_mtm = portfolio.mark_to_market(symbol="BTCUSDT", mark_price=51000.0, timestamp=self.now)
        self.assertEqual(p_state_mtm.equity, 10990.0)

    def test_portfolio_accounting_equation_invariant(self):
        """[Portfolio Boundary]: Strict Accounting Invariant Equity = Balance + Unrealized PnL MUST hold under all operations."""
        portfolio = Portfolio(initial_capital=10000.0)
        
        # Verify initial invariant
        self.assertAlmostEqual(portfolio.get_state(self.now).equity, portfolio.account.balance + 0.0, places=6)

        fill_buy = Fill(
            fill_id="fill_eq_inv_1",
            order_id="ord_eq_inv_1",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=2.0,
            price=60000.0,
            fee=20.0,
            timestamp=self.now,
        )
        portfolio.apply_fill(fill_buy)
        p_state = portfolio.mark_to_market(symbol="BTCUSDT", mark_price=65000.0, timestamp=self.now)

        # Equity MUST equal balance + unrealized PnL
        expected_unrealized = (65000.0 - 60000.0) * 2.0
        self.assertAlmostEqual(p_state.unrealized_pnl, expected_unrealized, places=6)
        self.assertAlmostEqual(p_state.equity, p_state.balance + expected_unrealized, places=6)


if __name__ == "__main__":
    unittest.main()
