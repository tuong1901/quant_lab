"""
[PURPOSE]: Domain Contract Tests verifying communication payloads across subsystem boundaries.
[DEPENDENCIES]: unittest, src.strategies, src.engine, src.environment, src.engine, src.evaluation.
"""

import unittest
from datetime import datetime, timezone

from src.strategies.signal import Signal, SignalAction
from src.strategies.context import StrategyContext
from src.strategies.ema import EMAStrategy
from src.trading.execution.order import Order, OrderSide, OrderType
from src.trading.execution.fill import Fill
from src.trading.execution.exceptions import QuantSystemError
from src.trading.portfolio.portfolio import Portfolio


class TestDomainContracts(unittest.TestCase):
    """
    [PURPOSE]: Contract verification tests between quantitative subsystems.
    """

    def setUp(self):
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_strategy_to_signal_contract(self):
        """[Contract: Strategy -> Signal]: Strategy.on_bar must produce valid Signal with matching timestamp."""
        strat = EMAStrategy(fast_period=20, slow_period=50)
        ctx = StrategyContext(
            timestamp=self.now,
            price=50000.0,
            position_side=None,
            features={"ema20": 51000.0, "ema50": 50000.0},
        )
        sig = strat.on_bar(ctx)
        self.assertIsInstance(sig, Signal)
        self.assertEqual(sig.timestamp, self.now)
        self.assertEqual(sig.action, SignalAction.LONG)

    def test_order_to_fill_contract(self):
        """[Contract: Order -> Fill]: Fill must preserve order symbol, side, and quantity semantics."""
        order = Order(
            order_id="ord_contract_01",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.5,
            created_at=self.now,
        )
        fill = Fill(
            fill_id="fill_contract_01",
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=50000.0,
            fee=10.0,
            timestamp=self.now,
        )
        self.assertEqual(fill.order_id, order.order_id)
        self.assertEqual(fill.symbol, order.symbol)
        self.assertEqual(fill.quantity, order.quantity)

    def test_fill_contract_rejects_negative_quantity(self):
        """[Contract: Fill]: Fill dataclass MUST reject non-positive quantities."""
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            Fill(
                fill_id="fill_bad_qty",
                order_id="ord_bad_qty",
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                quantity=-1.0,  # Invalid negative quantity contract
                price=50000.0,
                fee=5.0,
                timestamp=self.now,
            )


if __name__ == "__main__":
    unittest.main()
