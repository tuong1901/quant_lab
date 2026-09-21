"""
Unit tests for Core base exceptions (`src/core/exceptions.py`).
"""

import unittest


class TestCoreExceptions(unittest.TestCase):
    """
    [PURPOSE]: Test QuantSystemError base exception.
    """

    def test_quant_system_error_hierarchy(self):
        """Test that QuantSystemError inherits from Exception and can be caught as base exception."""
        from src.core.exceptions import QuantSystemError

        err = QuantSystemError("System root error")
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), "System root error")


if __name__ == "__main__":
    unittest.main()
