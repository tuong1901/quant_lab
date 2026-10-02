"""
[PURPOSE]: Environment Boundary Guard tests ensuring Environment is a pure composition container with complete state isolation.
[DEPENDENCIES]: unittest, ast, pathlib, src.environment.
"""

import ast
from pathlib import Path
import unittest

from src.config.loader import ConfigLoader
from src.trading.backtest import EnvironmentFactory


class TestEnvironmentBoundary(unittest.TestCase):
    """
    [PURPOSE]: Enforce Environment composition boundary invariants and state isolation.
    """

    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.environment_dir = self.project_root / "src" / "environment"

    def test_environment_ast_no_backtest_or_evaluation_imports(self):
        """[Environment Boundary]: Environment modules must not import Backtest Engine or Evaluation metrics."""
        forbidden_imports = {
            "src.evaluation",
            "src.experiments",
        }
        violations = []

        for file in self.environment_dir.glob("*.py"):
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
            self.fail("Environment Boundary Violation:\n" + "\n".join(violations))

    def test_environment_factory_isolation(self):
        """[Environment Boundary]: Environment Factory must instantiate isolated environments without global shared state."""
        loader = ConfigLoader(config_dir="config")
        config = loader.load_experiment("btc_rolling_1y")

        env_1 = EnvironmentFactory.create(config)
        env_2 = EnvironmentFactory.create(config)

        self.assertIsNot(env_1.portfolio, env_2.portfolio)
        self.assertIsNot(env_1.clock, env_2.clock)
        self.assertIsNot(env_1.execution, env_2.execution)
        self.assertIsNot(env_1.registry, env_2.registry)


if __name__ == "__main__":
    unittest.main()
