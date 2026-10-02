"""
[PURPOSE]: Unit tests for OHLC and Lower-Timeframe Replay FillModel implementations.
[DEPENDENCIES]: unittest, datetime, src.engine.
"""

import unittest
from datetime import datetime, timezone
from src.engine import (
    Order,
    OrderSide,
    OrderType,
    OHLCFillModel,
    LowerTimeframeReplayFillModel,
)

class TestFillModels(unittest.TestCase):
    def test_ohlc_market_and_limit_fills(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        bar = {"open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0, "timestamp": ts}

        # Market Order
        mkt_order = Order("ord_mkt", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, ts)
        model = OHLCFillModel(market_order_policy="open")
        fills = model.determine_fills(mkt_order, bar)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].price, 100.0)

        # Limit Buy Order (Limit=95.0, Low=90.0 -> Filled)
        limit_order = Order("ord_lim", "BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 1.0, ts, limit_price=95.0)
        fills_lim = model.determine_fills(limit_order, bar)
        self.assertEqual(len(fills_lim), 1)
        self.assertEqual(fills_lim[0].price, 95.0)

        # Limit Buy Order (Limit=85.0, Low=90.0 -> Not Filled)
        limit_unfilled = Order("ord_lim_unfilled", "BTCUSDT", OrderSide.BUY, OrderType.LIMIT, 1.0, ts, limit_price=85.0)
        self.assertEqual(len(model.determine_fills(limit_unfilled, bar)), 0)

    def test_ohlc_stop_order_fills(self):
        ts = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        bar = {"open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0, "timestamp": ts}

        # Stop Sell Order (Stop Loss 95.0, Low=90.0 -> Triggered)
        stop_order = Order("ord_stop", "BTCUSDT", OrderSide.SELL, OrderType.STOP, 1.0, ts, stop_price=95.0)
        model = OHLCFillModel()
        fills = model.determine_fills(stop_order, bar)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0].price, 95.0)
        self.assertEqual(fills[0].reason, "STOP_SELL_TRIGGERED")

    def test_lower_timeframe_replay_intrabar_sequence(self):
        """
        [TEST SPECIFICATION SECTION 10]:
        M15 Bar has High=110, Low=90.
        SL = 95, TP = 108.
        Replay M1 sequence to test exact timestamp triggering without guessing or lookahead.
        """
        ts_1000 = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
        ts_1001 = datetime(2025, 1, 1, 10, 1, tzinfo=timezone.utc)
        ts_1002 = datetime(2025, 1, 1, 10, 2, tzinfo=timezone.utc)
        ts_1003 = datetime(2025, 1, 1, 10, 3, tzinfo=timezone.utc)
        ts_1004 = datetime(2025, 1, 1, 10, 4, tzinfo=timezone.utc)

        # M1 Sequence A: Low = 94 at 10:03 (SL triggers FIRST before TP at 10:04)
        m1_sequence_a = [
            {"open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "timestamp": ts_1000},
            {"open": 102.0, "high": 104.0, "low": 101.0, "close": 103.0, "timestamp": ts_1001},
            {"open": 103.0, "high": 105.0, "low": 102.0, "close": 104.0, "timestamp": ts_1002},
            {"open": 104.0, "high": 105.0, "low": 94.0, "close": 96.0, "timestamp": ts_1003},   # SL 95 HIT HERE!
            {"open": 96.0, "high": 109.0, "low": 96.0, "close": 108.0, "timestamp": ts_1004},   # TP 108 later
        ]

        sl_order = Order("ord_sl", "BTCUSDT", OrderSide.SELL, OrderType.STOP, 1.0, ts_1000, stop_price=95.0)
        tp_order = Order("ord_tp", "BTCUSDT", OrderSide.SELL, OrderType.LIMIT, 1.0, ts_1000, limit_price=108.0)

        replay_model = LowerTimeframeReplayFillModel()

        # Execute SL check on sequence A -> Triggers at 10:03 timestamp
        sl_fills = replay_model.determine_fills(sl_order, m1_sequence_a)
        self.assertEqual(len(sl_fills), 1)
        self.assertEqual(sl_fills[0].timestamp, ts_1003)
        self.assertEqual(sl_fills[0].price, 95.0)

        # M1 Sequence B: TP 108 hit at 10:02 (TP triggers FIRST before SL at 10:03)
        m1_sequence_b = [
            {"open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0, "timestamp": ts_1000},
            {"open": 102.0, "high": 104.0, "low": 101.0, "close": 103.0, "timestamp": ts_1001},
            {"open": 103.0, "high": 109.0, "low": 102.0, "close": 108.0, "timestamp": ts_1002},  # TP 108 HIT HERE!
            {"open": 108.0, "high": 108.0, "low": 94.0, "close": 95.0, "timestamp": ts_1003},   # SL 95 later
        ]

        tp_fills = replay_model.determine_fills(tp_order, m1_sequence_b)
        self.assertEqual(len(tp_fills), 1)
        self.assertEqual(tp_fills[0].timestamp, ts_1002)
        self.assertEqual(tp_fills[0].price, 108.0)

if __name__ == "__main__":
    unittest.main()
