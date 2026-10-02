"""
Unit tests for local runtime Registry (`src/environment/registry.py`).
"""

import unittest


class TestRegistry(unittest.TestCase):
    """
    [PURPOSE]: Verify local Registry item registration, lookup, isolation, and duplicate key rejection.
    """

    def test_register_and_get(self):
        """Test registering and retrieving named runtime objects."""
        from src.trading.backtest import Registry

        reg = Registry()
        reg.register("clock_mode", "historical")

        self.assertTrue(reg.contains("clock_mode"))
        self.assertEqual(reg.get("clock_mode"), "historical")

    def test_require_existing_and_missing_key(self):
        """Test require returns value for existing key and raises MissingDependencyError for missing key."""
        from src.trading.backtest import Registry
        from src.trading.backtest import MissingDependencyError

        reg = Registry()
        reg.register("data_source", "parquet")

        self.assertEqual(reg.require("data_source"), "parquet")

        with self.assertRaises(MissingDependencyError):
            reg.require("non_existent_key")

    def test_duplicate_registration_raises_error(self):
        """Test that registering duplicate key raises EnvironmentConstructionError."""
        from src.trading.backtest import Registry
        from src.trading.backtest import EnvironmentConstructionError

        reg = Registry()
        reg.register("key1", "val1")

        with self.assertRaises(EnvironmentConstructionError):
            reg.register("key1", "val2")

    def test_registry_local_isolation(self):
        """Test that two Registry instances are completely isolated without global shared state."""
        from src.trading.backtest import Registry

        reg1 = Registry()
        reg2 = Registry()

        reg1.register("item", "reg1_value")
        self.assertTrue(reg1.contains("item"))
        self.assertFalse(reg2.contains("item"))


if __name__ == "__main__":
    unittest.main()
