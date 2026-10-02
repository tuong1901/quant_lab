"""
Unit tests for Evaluation Subsystem Exception hierarchy (`src/evaluation/exceptions.py`).
"""

import unittest

from src.trading.execution.exceptions import QuantSystemError


class TestEvaluationExceptions(unittest.TestCase):
    """
    [PURPOSE]: Verify Evaluation Exception inheritance and hierarchy.
    """

    def test_evaluation_error_hierarchy(self):
        """Test that EvaluationError inherits from QuantSystemError and custom exceptions inherit from EvaluationError."""
        from src.evaluation.exceptions import (
            EvaluationError,
            InvalidEvaluationError,
        )

        self.assertTrue(issubclass(EvaluationError, QuantSystemError))
        self.assertTrue(issubclass(InvalidEvaluationError, EvaluationError))


if __name__ == "__main__":
    unittest.main()
