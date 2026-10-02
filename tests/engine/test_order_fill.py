"""
[PURPOSE]: Unit tests for Order, Fill, and ExecutionResult models.
[DEPENDENCIES]: unittest, datetime, src.engine.
"""

import unittest
from datetime import datetime, timezone
from src.trading import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    Fill,
    ExecutionResult,
    InvalidOrderError,
)

class TestOrderFillModels(unittest.TestCase):
    def test_order_creation_and_immutability(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        order = Order(
            order_id="ord_001",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.5,
            limit_price=95000.0,
            created_at=ts,
        )

        self.assertEqual(order.order_id, "ord_001")
        self.assertEqual(order.remaining_quantity, 1.5)
        self.assertEqual(order.status, OrderStatus.CREATED)

        # Immutability check
        with self.assertRaises(AttributeError):
            order.quantity = 2.0

    def test_order_invalid_validations(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        # Invalid quantity
        with self.assertRaises(InvalidOrderError):
            Order("ord_002", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.0, ts)

        # Naive datetime
        with self.assertRaises(InvalidOrderError):
            Order("ord_003", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, datetime.now())

        # Missing limit_price on LIMIT order
        with self.assertRaises(InvalidOrderError):
            Order("ord_004", "BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 1.0, ts, limit_price=None)

    def test_order_status_transition(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        order = Order("ord_005", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 2.0, ts)
        updated = order.with_status(OrderStatus.PARTIALLY_FILLED, additional_filled_qty=0.5)

        self.assertEqual(updated.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(updated.filled_quantity, 0.5)
        self.assertEqual(updated.remaining_quantity, 1.5)
        self.assertTrue(updated.is_active)

    def test_fill_creation_and_execution_result(self):
        ts = datetime(2025, 1, 1, 10, 1, tzinfo=timezone.utc)
        f1 = Fill("fill_01", "ord_001", "BTCUSDT", OrderSide.BUY, quantity=1.0, price=95000.0, timestamp=ts, fee=4.0, slippage=10.0)
        f2 = Fill("fill_02", "ord_001", "BTCUSDT", OrderSide.BUY, quantity=0.5, price=96000.0, timestamp=ts, fee=2.0, slippage=5.0)

        result = ExecutionResult.from_fills("ord_001", OrderStatus.FILLED, [f1, f2])

        self.assertEqual(result.order_id, "ord_001")
        self.assertEqual(result.status, OrderStatus.FILLED)
        self.assertEqual(result.total_filled_quantity, 1.5)
        self.assertEqual(result.total_fee, 6.0)
        self.assertEqual(result.total_slippage, 15.0)
        # Average price = (1.0 * 95000 + 0.5 * 96000) / 1.5 = (95000 + 48000) / 1.5 = 143000 / 1.5 = 95333.33333333333
        self.assertAlmostEqual(result.average_fill_price, 95333.33333333333, places=4)

if __name__ == "__main__":
    unittest.main()
