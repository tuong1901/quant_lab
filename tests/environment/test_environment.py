"""
Unit tests for Environment domain model container (`src/environment/environment.py`).
"""

import unittest
from datetime import datetime, timezone

from src.trading.backtest import HistoricalClock
from src.config.loader import ConfigLoader


class TestEnvironment(unittest.TestCase):
    """
    [PURPOSE]: Verify Environment container immutability and component validation.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.exp_config = self.loader.load_experiment("btc_rolling_1y")
        self.clock = HistoricalClock(start_time=datetime(2024, 1, 1, tzinfo=timezone.utc))

    def test_environment_immutability(self):
        """Test that Environment dataclass attributes cannot be mutated after creation."""
        from src.trading.backtest import Registry
        from src.trading.backtest import Environment

        dummy_md = {"symbol": "BTCUSDT"}
        dummy_exec = {"engine": "mock"}
        dummy_port = {"account": "mock"}
        reg = Registry()

        env = Environment(
            clock=self.clock,
            market_data=dummy_md,
            execution=dummy_exec,
            portfolio=dummy_port,
            config=self.exp_config,
            registry=reg,
        )

        self.assertEqual(env.clock, self.clock)
        self.assertEqual(env.config, self.exp_config)

        with self.assertRaises(AttributeError):
            env.clock = HistoricalClock(start_time=datetime(2025, 1, 1, tzinfo=timezone.utc))

    def test_missing_clock_raises_error(self):
        """Test that missing clock component raises MissingDependencyError."""
        from src.trading.backtest import Registry
        from src.trading.backtest import Environment
        from src.trading.backtest import MissingDependencyError

        reg = Registry()
        with self.assertRaises(MissingDependencyError):
            Environment(
                clock=None,
                market_data={},
                execution={},
                portfolio={},
                config=self.exp_config,
                registry=reg,
            )


if __name__ == "__main__":
    unittest.main()
