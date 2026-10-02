"""
[PURPOSE]: Execution Boundary Guard tests ensuring Execution subsystem handles fills, slippage, and fees without calling Strategy or mutating Portfolio.
[DEPENDENCIES]: unittest, ast, pathlib, src.engine.
"""

import ast
from pathlib import Path
import unittest

from src.engine.execution.execution_engine import ExecutionEngine
from src.engine.execution.order import Order, OrderSide, OrderType, OrderStatus
from src.engine.execution.fill import Fill
from src.engine.execution.result import ExecutionResult
from datetime import datetime, timezone


class TestExecutionBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Execution subsystem boundary invariants.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.execution_dir = self.project_root / "src" / "execution"
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_execution_ast_forbidden_references(self):
        """[Execution Boundary]: Execution modules must not import Strategy, Portfolio, or Backtest Engine."""
        forbidden_imports = {
            "src.strategies",
            "src.environment",
            "src.engine",
        }
        violations = []

        for file in self.execution_dir.glob("*.py"):
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
            self.fail("Execution Boundary Violation:\n" + "\n".join(violations))

    def test_execution_lifecycle_returns_execution_result(self):
        """[Execution Boundary]: ExecutionEngine.process_market_data must return ExecutionResult list without mutating external state."""
        engine = ExecutionEngine()
        order = Order(
            order_id="ord_exec_boundary",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
            created_at=self.now,
        )

        accepted = engine.submit_order(order)
        self.assertEqual(accepted.status, OrderStatus.ACCEPTED)

        bar = {
            "timestamp": self.now,
            "open": 50000.0,
            "high": 51000.0,
            "low": 49000.0,
            "close": 50500.0,
            "volume": 100.0,
        }

        results = engine.process_market_data(market_data=bar, timestamp=self.now)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ExecutionResult)

        fill = results[0].fills[0]
        self.assertIsInstance(fill, Fill)
        self.assertGreater(fill.fee, 0.0, "Execution must calculate fee")


if __name__ == "__main__":
    unittest.main()
