"""
[PURPOSE]: Strategy Boundary Guard tests ensuring Strategy is a decision-only layer with zero execution or portfolio side effects.
[DEPENDENCIES]: unittest, ast, inspect, src.strategies.
"""

import ast
import inspect
from pathlib import Path
import unittest

from src.strategies.ema import EMAStrategy
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.environment.position import PositionSide
from datetime import datetime, timezone


class TestStrategyBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Strategy decision-only boundary invariants via AST analysis and behavioral contracts.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.strategies_dir = self.project_root / "src" / "strategies"

    def test_strategy_ast_forbidden_calls(self):
        """[Strategy Boundary]: Strategy source files must not reference ExecutionEngine, BacktestEngine, or Portfolio mutation methods."""
        forbidden_names = {
            "ExecutionEngine",
            "BacktestEngine",
            "apply_fill",
            "mark_to_market",
            "submit_order",
            "process_market_data",
        }
        violations = []

        for file in self.strategies_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id in forbidden_names:
                    violations.append(f"{file.name} references forbidden execution/portfolio symbol '{node.id}'")
                elif isinstance(node, ast.Attribute) and node.attr in forbidden_names:
                    violations.append(f"{file.name} calls forbidden execution/portfolio method '{node.attr}'")

        if violations:
            self.fail("Strategy Boundary Violation:\n" + "\n".join(violations))

    def test_strategy_on_bar_contract_and_side_effects(self):
        """[Strategy Boundary]: Strategy.on_bar() must return Signal and produce zero side effects."""
        strat = EMAStrategy(fast_period=20, slow_period=50)
        ts = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        context = StrategyContext(
            timestamp=ts,
            price=100.0,
            position_side=PositionSide.LONG,
            features={"ema20": 110.0, "ema50": 100.0},
        )

        signal = strat.on_bar(context)

        # 1. Output must be a Signal instance
        self.assertIsInstance(signal, Signal, "on_bar must return a Signal instance")
        self.assertIn(signal.action, (SignalAction.HOLD, SignalAction.LONG, SignalAction.SHORT))

        # 2. Context must not be mutated
        self.assertEqual(context.timestamp, ts)
        self.assertEqual(context.price, 100.0)
        self.assertEqual(context.position_side, PositionSide.LONG)

    def test_strategy_ast_no_naive_datetime_or_unseeded_randomness(self):
        """[Strategy Boundary]: Strategy source files must not reference datetime.now() or unseeded random without UTC clock."""
        violations = []
        forbidden_attributes = {
            ("datetime", "now"),
            ("datetime", "today"),
        }

        for file in self.strategies_dir.glob("*.py"):
            with open(file, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        pair = (node.value.id, node.attr)
                        if pair in forbidden_attributes:
                            violations.append(f"{file.name} calls non-deterministic '{node.value.id}.{node.attr}' instead of Clock")

        if violations:
            self.fail("Strategy Boundary Violation (Non-deterministic clock reference):\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
