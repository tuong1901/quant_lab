"""
Unit tests for Backtest Engine exception hierarchy (`src/backtest/exceptions.py`).
"""

import unittest

from src.trading.execution.exceptions import QuantSystemError


class TestBacktestExceptions(unittest.TestCase):
    """
    [PURPOSE]: Verify Backtest Exception inheritance and hierarchy.
    """

    def test_backtest_error_hierarchy(self):
        """Test that BacktestError inherits from QuantSystemError and custom exceptions inherit from BacktestError."""
        from src.trading.execution.exceptions import (
            BacktestError,
            BacktestExecutionError,
            InvalidSimulationStateError,
        )

        self.assertTrue(issubclass(BacktestError, QuantSystemError))
        self.assertTrue(issubclass(BacktestExecutionError, BacktestError))
        self.assertTrue(issubclass(InvalidSimulationStateError, BacktestError))


if __name__ == "__main__":
    unittest.main()
