"""
Integration test for Environment Subsystem (`src/environment/`).
"""

import unittest
from datetime import datetime, timezone

from src.config.loader import ConfigLoader
from src.experiments.run import ExperimentRun
from src.experiments.window import TimeWindow


class TestEnvironmentIntegration(unittest.TestCase):
    """
    [PURPOSE]: Verify end-to-end integration between Config -> Factory -> Environment -> ExecutionContext.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.exp_config = self.loader.load_experiment("btc_rolling_1y")

    def test_full_environment_lifecycle_pipeline(self):
        """Test creating Environment and ExecutionContext from Config."""
        from src.trading import (
            EnvironmentFactory,
            Environment,
            ExecutionContext,
        )

        # 1. Factory builds Environment
        env = EnvironmentFactory.create(config=self.exp_config)
        self.assertIsInstance(env, Environment)

        # 2. Build ExperimentRun
        window = TimeWindow(
            warmup_start=datetime(2023, 12, 1, tzinfo=timezone.utc),
            execution_start=env.config.time.start,
            execution_end=env.config.time.end,
        )
        run = ExperimentRun(run_id="run_001", seed=42, window=window)

        # 3. Create ExecutionContext for run
        ctx = ExecutionContext(
            clock=env.clock,
            run=run,
            dataset_id=env.config.strategy_dataset.name,
            execution_id=env.config.execution.name,
        )

        self.assertEqual(ctx.clock.now(), env.config.time.start)
        self.assertEqual(ctx.run.run_id, "run_001")


if __name__ == "__main__":
    unittest.main()
