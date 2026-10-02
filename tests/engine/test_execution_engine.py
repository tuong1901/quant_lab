"""
[PURPOSE]: Unit tests for ExecutionEngine orchestration, partial fills, event audit log, and 100% determinism.
[DEPENDENCIES]: unittest, datetime, src.engine.
"""

import unittest
from datetime import datetime, timezone
from src.engine import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    ExecutionEngine,
    OHLCFillModel,
    FixedSlippageModel,
    PercentageFeeModel,
    HistoricalBroker,
)

class TestExecutionEngine(unittest.TestCase):
    def test_execution_engine_full_flow(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        engine = ExecutionEngine(
            fill_model=OHLCFillModel(market_order_policy="open"),
            slippage_model=FixedSlippageModel(bps=10.0), # 10 bps
            fee_model=PercentageFeeModel(maker_bps=2.0, taker_bps=4.0) # 4 bps taker
        )

        # 1. Submit Market Order
        order = Order("ord_001", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, quantity=1.0, created_at=ts)
        submitted = engine.submit_order(order)
        self.assertEqual(submitted.status, OrderStatus.ACCEPTED)
        self.assertIn("ord_001", engine.active_orders)

        # 2. Process Market Data Bar (Open=100000, High=105000, Low=99000, Close=102000)
        bar = {"open": 100000.0, "high": 105000.0, "low": 99000.0, "close": 102000.0, "timestamp": ts}
        results = engine.process_market_data(bar, timestamp=ts)

        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.order_id, "ord_001")
        self.assertEqual(res.status, OrderStatus.FILLED)
        self.assertEqual(res.total_filled_quantity, 1.0)

        # Verify slippage: 100000 * 1.0010 = 100100.0
        self.assertEqual(res.average_fill_price, 100100.0)
        # Verify fee: 100100 * 0.0004 = 40.04
        self.assertAlmostEqual(res.total_fee, 40.04, places=2)

        # Order moved from active to completed
        self.assertNotIn("ord_001", engine.active_orders)
        self.assertIn("ord_001", engine.completed_orders)

        # Audit events check
        events = engine.get_audit_events()
        event_types = [e.event_type for e in events]
        self.assertIn("ORDER_SUBMITTED", event_types)
        self.assertIn("ORDER_ACCEPTED", event_types)
        self.assertIn("FILL_CREATED", event_types)
        self.assertIn("ORDER_FILLED", event_types)

    def test_execution_engine_determinism(self):
        """
        [SPECIFICATION SECTION 23]: Determinism Verification.
        Run identical execution simulation twice -> MUST produce identical order lifecycle, fills, prices, fees, timestamps.
        """
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        bar = {"open": 50000.0, "high": 52000.0, "low": 48000.0, "close": 51000.0, "timestamp": ts}

        def run_sim():
            engine = ExecutionEngine(
                fill_model=OHLCFillModel(),
                slippage_model=FixedSlippageModel(bps=5.0),
                fee_model=PercentageFeeModel(taker_bps=4.0)
            )
            broker = HistoricalBroker(engine)
            order = Order("ord_det_1", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, quantity=2.0, created_at=ts)
            res = broker.execute_orders([order], bar)
            return res, engine.get_audit_events()

        res1, events1 = run_sim()
        res2, events2 = run_sim()

        # Check equality of results and audit events
        self.assertEqual(res1, res2)
        self.assertEqual(events1, events2)

if __name__ == "__main__":
    unittest.main()
