"""Critical execution contracts for causal T+1 order handling."""

from datetime import datetime, timedelta, timezone
import unittest

import pandas as pd

from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.trading.backtest import BacktestEngine
from src.trading.execution.broker import ExecutionEngine
from src.trading.execution.fees import PercentageFeeModel
from src.trading.execution.order import Order, OrderSide, OrderType
from src.trading.execution.slippage import FixedSlippageModel


UTC = timezone.utc
START_TIME = datetime(2026, 10, 5, 10, 15, tzinfo=UTC)


def make_order(
    side: OrderSide,
    order_type: OrderType = OrderType.MARKET,
    price: float = 0.0,
    quantity: float = 1.0,
) -> Order:
    """
    [PURPOSE]: Create a valid deterministic order for execution contract tests.
    [DEPENDENCIES]: Used only by tests in this module.
    [ARGS]: side, order_type, price, quantity — order values under test.
    [RETURNS]: New created Order with a fixed UTC timestamp.
    [SIDE EFFECTS]: None.
    """
    return Order(
        order_id=f"order-{side.value}-{order_type.value}-{price}-{quantity}",
        symbol="BTCUSDT",
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        created_at=START_TIME,
    )


class FirstBarLongStrategy:
    """Strategy that signals LONG only on its first observed candle."""

    strategy_id = "execution-contract-long"

    def __init__(self) -> None:
        self.signal_timestamp = None

    def on_bar(self, context: StrategyContext) -> Signal:
        """
        [PURPOSE]: Emit one LONG signal at the first candle close.
        [DEPENDENCIES]: Called by BacktestEngine.
        [ARGS]: context — closed-candle strategy context.
        [RETURNS]: LONG on first call, HOLD thereafter.
        [SIDE EFFECTS]: Stores the first signal timestamp for assertions.
        """
        if self.signal_timestamp is None:
            self.signal_timestamp = context.timestamp
            return Signal(timestamp=context.timestamp, action=SignalAction.LONG)
        return Signal(timestamp=context.timestamp, action=SignalAction.HOLD)


class TestExecutionTimingContracts(unittest.TestCase):
    """EX-01 to EX-03: a decision at candle T executes only at candle T+1."""

    def _run_first_bar_long(self, next_open: float):
        strategy = FirstBarLongStrategy()
        frame = pd.DataFrame(
            [
                {
                    "timestamp": START_TIME,
                    "open": 95.0,
                    "high": 101.0,
                    "low": 94.0,
                    "close": 100.0,
                    "volume": 1.0,
                },
                {
                    "timestamp": START_TIME + timedelta(minutes=15),
                    "open": next_open,
                    "high": next_open + 5.0,
                    "low": next_open - 2.0,
                    "close": next_open + 3.0,
                    "volume": 1.0,
                },
            ]
        )
        return strategy, BacktestEngine(strategy=strategy).run(frame)

    def test_exec_time_001_and_002_market_order_fills_at_next_open(self):
        strategy, result = self._run_first_bar_long(next_open=105.0)

        self.assertEqual(len(result.orders), 1)
        self.assertEqual(len(result.fills), 1)
        self.assertEqual(result.orders[0].created_at, strategy.signal_timestamp)
        self.assertGreater(result.fills[0].timestamp, result.orders[0].created_at)
        self.assertEqual(result.fills[0].timestamp, START_TIME + timedelta(minutes=15))
        self.assertEqual(result.fills[0].price, 105.0)

    def test_strategy_decision_does_not_depend_on_next_open(self):
        strategy_a, result_a = self._run_first_bar_long(next_open=105.0)
        strategy_b, result_b = self._run_first_bar_long(next_open=500.0)

        self.assertEqual(strategy_a.signal_timestamp, strategy_b.signal_timestamp)
        self.assertEqual(result_a.orders[0].side, result_b.orders[0].side)
        self.assertEqual(result_a.orders[0].created_at, result_b.orders[0].created_at)
        self.assertEqual(result_a.fills[0].price, 105.0)
        self.assertEqual(result_b.fills[0].price, 500.0)


class TestExecutionEngineContracts(unittest.TestCase):
    """EX-04 to EX-07: price, fees, limit eligibility, and pending-order lifecycle."""

    def test_market_buy_and_sell_apply_adverse_slippage_and_fee_to_fill_price(self):
        engine = ExecutionEngine(
            slippage_model=FixedSlippageModel(slippage_bps=10.0),
            fee_model=PercentageFeeModel(maker_bps=0.0, taker_bps=10.0),
        )
        buy_order = make_order(OrderSide.BUY, quantity=2.0)
        sell_order = make_order(OrderSide.SELL, quantity=2.0)
        engine.submit_order(buy_order)
        engine.submit_order(sell_order)

        results = engine.process_market_data(
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            START_TIME + timedelta(minutes=15),
        )
        fills = {result.order.side: result.fills[0] for result in results}

        self.assertEqual(fills[OrderSide.BUY].price, 100.1)
        self.assertEqual(fills[OrderSide.SELL].price, 99.9)
        self.assertAlmostEqual(fills[OrderSide.BUY].fee, 0.2002)
        self.assertAlmostEqual(fills[OrderSide.SELL].fee, 0.1998)

    def test_market_falls_back_to_close_when_open_is_missing(self):
        engine = ExecutionEngine()
        engine.submit_order(make_order(OrderSide.BUY))

        results = engine.process_market_data(
            {"high": 109.0, "low": 99.0, "close": 105.0},
            START_TIME + timedelta(minutes=15),
        )

        self.assertEqual(results[0].fills[0].price, 105.0)

    def test_filled_order_is_removed_and_cannot_fill_twice(self):
        engine = ExecutionEngine()
        order = make_order(OrderSide.BUY)
        engine.submit_order(order)
        first_results = engine.process_market_data(
            {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0},
            START_TIME + timedelta(minutes=15),
        )
        second_results = engine.process_market_data(
            {"open": 101.0, "high": 102.0, "low": 100.0, "close": 101.0},
            START_TIME + timedelta(minutes=30),
        )

        self.assertEqual(len(first_results), 1)
        self.assertEqual(first_results[0].order.status.value, "FILLED")
        self.assertNotIn(order.order_id, engine.pending_orders)
        self.assertEqual(second_results, [])

    def test_limit_orders_fill_only_on_touch_and_at_exact_limit_price(self):
        cases = [
            (OrderSide.BUY, 99.0, 110.0, True),
            (OrderSide.BUY, 100.0, 110.0, True),
            (OrderSide.BUY, 101.0, 110.0, False),
            (OrderSide.SELL, 90.0, 101.0, True),
            (OrderSide.SELL, 90.0, 100.0, True),
            (OrderSide.SELL, 90.0, 99.0, False),
        ]
        for side, low, high, should_fill in cases:
            with self.subTest(side=side, low=low, high=high):
                engine = ExecutionEngine(slippage_model=FixedSlippageModel(slippage_bps=100.0))
                order = make_order(side, OrderType.LIMIT, price=100.0)
                engine.submit_order(order)
                results = engine.process_market_data(
                    {"open": 105.0, "high": high, "low": low, "close": 102.0},
                    START_TIME + timedelta(minutes=15),
                )

                self.assertEqual(bool(results), should_fill)
                if should_fill:
                    self.assertEqual(results[0].fills[0].price, 100.0)
                else:
                    self.assertIn(order.order_id, engine.pending_orders)

