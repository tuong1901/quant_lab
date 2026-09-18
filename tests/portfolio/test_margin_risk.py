"""
[PURPOSE]: Unit tests for Margin accounting and RiskManager pre-execution validation.
[DEPENDENCIES]: unittest, datetime, src.execution, src.portfolio.
"""

import unittest
from datetime import datetime, timezone
from src.execution import Order, OrderSide, OrderType
from src.portfolio import (
    Portfolio,
    SimpleMarginModel,
    RiskManager,
    RiskDecisionResult,
)

class TestMarginAndRiskManager(unittest.TestCase):
    def test_margin_calculation(self):
        margin_model = SimpleMarginModel()
        # 30,000 notional with 5x leverage -> 6,000 initial margin
        init_margin = margin_model.calculate_initial_margin(position_notional=30000.0, leverage=5.0)
        self.assertEqual(init_margin, 60000.0 / 10.0)

    def test_risk_manager_allow_and_reject(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        portfolio = Portfolio(initial_capital=10000.0, leverage=5.0)
        state = portfolio.get_state(ts)

        risk_mgr = RiskManager(
            allow_short=False,
            max_position_size=2.0,
            max_notional=50000.0,
            max_leverage=5.0
        )

        # 1. Valid Buy Order (0.5 BTC @ 60,000 = 30,000 notional <= 50,000, margin 6000 <= available 10000)
        valid_order = Order("o1", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, quantity=0.5, created_at=ts)
        decision1 = risk_mgr.validate_order(valid_order, state, mark_price=60000.0)
        self.assertTrue(decision1.is_allowed)

        # 2. Reject Short Order (Shorting disabled)
        short_order = Order("o2", "BTCUSDT", OrderSide.SELL, OrderType.MARKET, quantity=0.5, created_at=ts)
        decision2 = risk_mgr.validate_order(short_order, state, mark_price=60000.0)
        self.assertFalse(decision2.is_allowed)
        self.assertIn("Shorting is disabled", decision2.reason)

        # 3. Reject Max Notional (1.0 BTC @ 60,000 = 60,000 notional > 50,000)
        large_notional_order = Order("o3", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, quantity=1.0, created_at=ts)
        decision3 = risk_mgr.validate_order(large_notional_order, state, mark_price=60000.0)
        self.assertFalse(decision3.is_allowed)
        self.assertIn("max_notional", decision3.reason)

        # 4. Reject Max Position Size (2.5 BTC > 2.0 max_position_size)
        large_qty_order = Order("o4", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, quantity=2.5, created_at=ts)
        decision4 = risk_mgr.validate_order(large_qty_order, state, mark_price=10000.0)
        self.assertFalse(decision4.is_allowed)
        self.assertIn("max_position_size", decision4.reason)

if __name__ == "__main__":
    unittest.main()
