"""
Unit tests for EnvironmentFactory assembly engine (`src/environment/factory.py`).
"""

import unittest
from datetime import datetime, timezone

from src.config.loader import ConfigLoader
from src.core.clock import HistoricalClock


class TestEnvironmentFactory(unittest.TestCase):
    """
    [PURPOSE]: Verify EnvironmentFactory assembly of runtime environment from typed ExperimentConfig.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.exp_config = self.loader.load_experiment("btc_rolling_1y")

    def test_factory_create_environment_from_config(self):
        """Test creating a complete Environment instance from an ExperimentConfig."""
        from src.environment.factory import EnvironmentFactory
        from src.environment.environment import Environment

        env = EnvironmentFactory.create(config=self.exp_config)

        self.assertIsInstance(env, Environment)
        self.assertIsInstance(env.clock, HistoricalClock)
        self.assertEqual(env.clock.now(), self.exp_config.time.start)
        self.assertEqual(env.config, self.exp_config)
        self.assertIsNotNone(env.execution)
        self.assertIsNotNone(env.portfolio)
        self.assertIsNotNone(env.registry)

    def test_factory_dependency_injection_overrides(self):
        """Test that passing pre-constructed dependencies directly into factory overrides default construction."""
        from src.environment.factory import EnvironmentFactory

        custom_clock = HistoricalClock(start_time=datetime(2025, 6, 1, tzinfo=timezone.utc))
        custom_exec = {"custom": "execution_engine"}
        custom_port = {"custom": "portfolio"}

        env = EnvironmentFactory.create(
            config=self.exp_config,
            clock=custom_clock,
            execution_engine=custom_exec,
            portfolio=custom_port,
        )

        self.assertEqual(env.clock, custom_clock)
        self.assertEqual(env.execution, custom_exec)
        self.assertEqual(env.portfolio, custom_port)


if __name__ == "__main__":
    unittest.main()
