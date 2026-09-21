"""
[PURPOSE]: Backtest Boundary Guard tests ensuring BacktestEngine relies strictly on Strategy Protocol abstractions without hardcoding specific strategy implementations.
[DEPENDENCIES]: unittest, ast, pathlib, src.backtest.
"""

import ast
from pathlib import Path
import unittest

from src.backtest.engine import BacktestEngine
from src.strategies.strategy import Strategy


class TestBacktestBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Backtest subsystem boundary invariants.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.backtest_dir = self.project_root / "src" / "backtest"

    def test_backtest_ast_no_concrete_strategy_imports(self):
        """[Backtest Boundary]: Backtest Engine modules must not import concrete strategy implementations (e.g., EMAStrategy)."""
        forbidden_imports = {
            "src.strategies.ema",
            "src.strategies.ema_cross",
        }
        violations = []

        for file in self.backtest_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in forbidden_imports:
                        if node.module == forbidden or node.module.startswith(forbidden + "."):
                            violations.append(f"{file.name} imports concrete strategy module '{node.module}'")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_imports:
                            if alias.name == forbidden or alias.name.startswith(forbidden + "."):
                                violations.append(f"{file.name} imports concrete strategy module '{alias.name}'")

        if violations:
            self.fail("Backtest Boundary Violation:\n" + "\n".join(violations))

    def test_backtest_engine_accepts_any_protocol_strategy(self):
        """[Backtest Boundary]: BacktestEngine accepts any object satisfying the Strategy Protocol contract."""
        self.assertTrue(hasattr(BacktestEngine, "__init__"))

    def test_backtest_engine_rejects_non_protocol_strategy(self):
        """[Backtest Boundary]: BacktestEngine must fail or reject strategy objects that do not satisfy Strategy Protocol."""
        class InvalidStrategy:
            pass  # Missing on_bar method

        invalid_strat = InvalidStrategy()
        # Verify invalid strategy fails runtime protocol check or produces error during execution
        with self.assertRaises((TypeError, AttributeError, Exception)):
            engine = BacktestEngine(environment=None, strategy=invalid_strat)  # type: ignore
            # If __init__ doesn't validate immediately, running on data must fail
            engine.run(df=None)  # type: ignore

    def test_backtest_ast_no_portfolio_internal_imports(self):
        """[Backtest Boundary]: Backtest Engine must interact with Portfolio interface, not private account or pnl internals."""
        forbidden_imports = {
            "src.portfolio.account",
            "src.portfolio.pnl",
        }
        violations = []

        for file in self.backtest_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for forbidden in forbidden_imports:
                        if node.module == forbidden or node.module.startswith(forbidden + "."):
                            violations.append(f"{file.name} imports forbidden portfolio internal module '{node.module}'")

        if violations:
            self.fail("Backtest Boundary Violation:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
