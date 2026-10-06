"""Unit tests for execution cost models that are not yet production-wired."""

from datetime import datetime, timezone
import unittest

from src.trading.execution.funding import PerpetualFundingModel
from src.trading.execution.order import Order, OrderSide, OrderType
from src.trading.execution.slippage import FixedSlippageModel, VolatilitySlippageModel


def make_order(side: OrderSide) -> Order:
    """
    [PURPOSE]: Create a valid market order for independent cost-model tests.
    [DEPENDENCIES]: Used only by tests in this module.
    [ARGS]: side — BUY or SELL direction to test.
    [RETURNS]: A created market order with a fixed UTC timestamp.
    [SIDE EFFECTS]: None.
    """
    return Order(
        order_id=f"cost-model-{side.value}",
        symbol="BTCUSDT",
        side=side,
        order_type=OrderType.MARKET,
        quantity=1.0,
        created_at=datetime(2026, 10, 5, tzinfo=timezone.utc),
    )


class TestExecutionCostModels(unittest.TestCase):
    """Unit coverage for independently usable execution-cost components."""

    def test_zero_slippage_is_identity_and_negative_configuration_is_rejected(self):
        buy = make_order(OrderSide.BUY)
        self.assertEqual(FixedSlippageModel(0.0).calculate_execution_price(buy, 100.0), 100.0)
        with self.assertRaises(ValueError):
            FixedSlippageModel(-1.0)
        with self.assertRaises(ValueError):
            VolatilitySlippageModel(-0.1)

    def test_volatility_slippage_uses_atr_when_called_directly(self):
        buy = make_order(OrderSide.BUY)
        sell = make_order(OrderSide.SELL)
        model = VolatilitySlippageModel(atr_factor=0.1)

        self.assertEqual(model.calculate_execution_price(buy, 100.0, atr_value=10.0), 101.0)
        self.assertEqual(model.calculate_execution_price(sell, 100.0, atr_value=10.0), 99.0)

    def test_funding_formula_handles_zero_and_elapsed_time(self):
        model = PerpetualFundingModel(funding_rate_8h=0.001)

        self.assertEqual(model.calculate_funding_fee(notional_value=0.0), 0.0)
        self.assertEqual(model.calculate_funding_fee(notional_value=1000.0, bars_held=0), 0.0)
        self.assertEqual(
            model.calculate_funding_fee(notional_value=1000.0, bars_held=32, bar_timeframe_minutes=15),
            1.0,
        )
