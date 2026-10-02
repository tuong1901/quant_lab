"""
Unit tests for Strategy Subsystem Exception hierarchy (`src/strategies/exceptions.py`).
"""

import unittest

from src.trading.execution.exceptions import QuantSystemError


class TestStrategyExceptions(unittest.TestCase):
    """
    [PURPOSE]: Verify Strategy Exception inheritance and hierarchy.
    """

    def test_strategy_error_hierarchy(self):
        """Test that StrategyError inherits from QuantSystemError and custom exceptions inherit from StrategyError."""
        from src.strategies.exceptions import (
            StrategyError,
            InvalidSignalError,
            StrategyContextError,
        )

        self.assertTrue(issubclass(StrategyError, QuantSystemError))
        self.assertTrue(issubclass(InvalidSignalError, StrategyError))
        self.assertTrue(issubclass(StrategyContextError, StrategyError))


if __name__ == "__main__":
    unittest.main()
