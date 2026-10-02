"""
Unit tests for Core Entity ID System (`src/core/ids.py`).
"""

import unittest


class TestCoreIds(unittest.TestCase):
    """
    [PURPOSE]: Verify immutable ID wrappers, type distinctions, and string representation.
    """

    def test_id_creation_and_string_representation(self):
        """Test creating IDs with string values and str() formatting."""
        from src.trading.execution.order import OrderId, FillId, EventId
        from src.strategies.strategy import StrategyId

        order_id = OrderId("ord_001")
        self.assertEqual(str(order_id), "ord_001")
        self.assertEqual(order_id.value, "ord_001")

        fill_id = FillId("fill_001")
        self.assertEqual(str(fill_id), "fill_001")

    def test_id_immutability(self):
        """Test that ID instance value cannot be mutated."""
        from src.trading.execution.order import OrderId

        order_id = OrderId("ord_001")
        with self.assertRaises(AttributeError):
            order_id.value = "ord_002"

    def test_type_distinction_between_different_id_classes(self):
        """Test that OrderId and StrategyId with the same string value are NOT equal."""
        from src.trading.execution.order import OrderId
        from src.strategies.strategy import StrategyId

        order_id = OrderId("123")
        strat_id = StrategyId("123")
        self.assertNotEqual(order_id, strat_id)

    def test_same_id_class_equality(self):
        """Test that two OrderId instances with identical values ARE equal."""
        from src.trading.execution.order import OrderId

        id1 = OrderId("ord_001")
        id2 = OrderId("ord_001")
        self.assertEqual(id1, id2)

    def test_id_generation(self):
        """Test auto-generating unique ID instances."""
        from src.trading.execution.order import EventId

        evt1 = EventId.generate()
        evt2 = EventId.generate()
        self.assertIsNotNone(evt1.value)
        self.assertNotEqual(evt1, evt2)


if __name__ == "__main__":
    unittest.main()
