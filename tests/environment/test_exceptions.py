"""
Unit tests for Environment subsystem exceptions (`src/environment/exceptions.py`).
"""

import unittest
from src.trading.execution.exceptions import QuantSystemError


class TestEnvironmentExceptions(unittest.TestCase):
    """
    [PURPOSE]: Verify EnvironmentError inheritance from QuantSystemError.
    """

    def test_environment_error_hierarchy(self):
        """Test that EnvironmentError inherits from QuantSystemError."""
        from src.trading.portfolio.exceptions import (
            EnvironmentError,
            EnvironmentConstructionError,
            MissingDependencyError,
            EnvironmentValidationError,
        )

        err = EnvironmentError("Environment root error")
        self.assertIsInstance(err, QuantSystemError)
        self.assertEqual(str(err), "Environment root error")

        const_err = EnvironmentConstructionError("Construction failed")
        self.assertIsInstance(const_err, EnvironmentError)

        missing_err = MissingDependencyError("Missing clock")
        self.assertIsInstance(missing_err, EnvironmentError)

        val_err = EnvironmentValidationError("Validation failed")
        self.assertIsInstance(val_err, EnvironmentError)


if __name__ == "__main__":
    unittest.main()
