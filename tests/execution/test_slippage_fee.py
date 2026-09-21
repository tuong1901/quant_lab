"""
[PURPOSE]: Unit tests for SlippageModel and FeeModel implementations.
[DEPENDENCIES]: unittest, datetime, src.execution.
"""

import unittest
from datetime import datetime, timezone
from src.execution import (
    Order,
    OrderSide,
    OrderType,
    FixedSlippageModel,
    VolatilitySlippageModel,
    PercentageFeeModel,
    SlippageError,
    FeeError,
)

class TestSlippageAndFee(unittest.TestCase):
    def test_fixed_slippage_model(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        buy_order = Order("ord_b", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, ts)
        sell_order = Order("ord_s", "BTCUSDT", OrderSide.SELL, OrderType.MARKET, 1.0, ts)

        # 10 bps slippage (0.1%)
        slip_model = FixedSlippageModel(bps=10.0)

        # BUY theoretical = 100000 -> actual = 100000 * 1.0010 = 100100
        actual_buy = slip_model.apply(buy_order, theoretical_price=100000.0)
        self.assertEqual(actual_buy, 100100.0)

        # SELL theoretical = 100000 -> actual = 100000 * 0.9990 = 99900
        actual_sell = slip_model.apply(sell_order, theoretical_price=100000.0)
        self.assertEqual(actual_sell, 99900.0)

    def test_volatility_slippage_model(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        buy_order = Order("ord_b", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, ts)
        slip_model = VolatilitySlippageModel(factor=0.2)

        market_ctx = {"atr": 50.0}
        # BUY theoretical = 100.0, impact = 50 * 0.2 = 10.0 -> actual = 110.0
        actual_price = slip_model.apply(buy_order, theoretical_price=100.0, market_context=market_ctx)
        self.assertEqual(actual_price, 110.0)

    def test_percentage_fee_model(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        mkt_order = Order("ord_mkt", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 2.0, ts)
        limit_order = Order("ord_lim", "BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 2.0, ts, limit_price=50000.0)

        # Taker 4 bps (0.04%), Maker 2 bps (0.02%)
        fee_model = PercentageFeeModel(maker_bps=2.0, taker_bps=4.0)

        # Market order fill nominal = 50000 * 2 = 100000 -> taker fee = 100000 * 0.0004 = 40.0
        fee_taker = fee_model.calculate(mkt_order, fill_price=50000.0, fill_quantity=2.0, is_maker=False)
        self.assertEqual(fee_taker, 40.0)

        # Limit order fill nominal = 50000 * 2 = 100000 -> maker fee = 100000 * 0.0002 = 20.0
        fee_maker = fee_model.calculate(limit_order, fill_price=50000.0, fill_quantity=2.0, is_maker=True)
        self.assertEqual(fee_maker, 20.0)

if __name__ == "__main__":
    unittest.main()
