"""
[PURPOSE]: Evaluation Boundary Guard tests ensuring Evaluation subsystem reads BacktestResult without depending on runtime modules.
[DEPENDENCIES]: unittest, ast, pathlib, src.evaluation.
"""

import ast
from pathlib import Path
import unittest

from src.evaluation.metrics import BasicMetrics, calculate_basic_metrics
from src.engine.backtest_result import BacktestResult
from src.environment.portfolio_state import PortfolioState
from datetime import datetime, timezone


class TestEvaluationBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Evaluation subsystem boundary invariants.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.evaluation_dir = self.project_root / "src" / "evaluation"

    def test_evaluation_ast_no_runtime_imports(self):
        """[Evaluation Boundary]: Evaluation modules must not import Portfolio, Environment, or Strategy runtime modules."""
        forbidden_imports = {
            "src.environment",
            "src.strategies",
            "src.data",
        }
        violations = []

        for file in self.evaluation_dir.glob("*.py"):
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
            self.fail("Evaluation Boundary Violation:\n" + "\n".join(violations))

    def test_evaluation_immutability_and_pure_calculation(self):
        """[Evaluation Boundary]: calculate_basic_metrics must return frozen BasicMetrics without mutating BacktestResult."""
        now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        p_state = PortfolioState(
            timestamp=now,
            balance=10000.0,
            equity=10000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            fees_paid=0.0,
            funding_paid=0.0,
            used_margin=0.0,
            available_margin=10000.0,
            positions={},
        )
        result = BacktestResult(
            run_id="run_eval_boundary",
            strategy_id="strat_eval_boundary",
            dataset_id="ds_eval_boundary",
            initial_capital=10000.0,
            bars_processed=10,
            final_timestamp=now,
            signals=(),
            orders=(),
            fills=(),
            portfolio_history=(p_state,),
            final_portfolio=p_state,
        )

        metrics = calculate_basic_metrics(result)
        self.assertIsInstance(metrics, BasicMetrics)
        self.assertEqual(metrics.initial_capital, 10000.0)
        self.assertEqual(metrics.final_equity, 10000.0)
        self.assertEqual(metrics.net_pnl, 0.0)


if __name__ == "__main__":
    unittest.main()
