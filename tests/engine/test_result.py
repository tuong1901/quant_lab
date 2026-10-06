"""
Unit tests for BacktestResult container (`src/backtest/result.py`).
"""

import unittest
from datetime import datetime, timezone

from src.strategies.signal import Signal, SignalAction
from src.trading.execution.order import Order, OrderSide, OrderType
from src.trading.execution.fill import Fill
from src.trading.portfolio.portfolio import PortfolioState
from src.trading.portfolio.account import Account


class TestBacktestResult(unittest.TestCase):
    """
    [PURPOSE]: Verify BacktestResult container immutability, metadata, and properties.
    """

    def setUp(self):
        self.now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.signal = Signal(timestamp=self.now, action=SignalAction.LONG, strategy_id="ema_20_50")
        self.order = Order(
            order_id="ord_001",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
            created_at=self.now,
        )
        self.fill = Fill(
            fill_id="fill_001",
            order_id="ord_001",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=40000.0,
            timestamp=self.now,
            fee=8.0,
        )
        self.portfolio_state = PortfolioState(
            timestamp=self.now,
            balance=10000.0,
            equity=10000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            fees_paid=8.0,
            funding_paid=0.0,
            used_margin=0.0,
            available_margin=10000.0,
        )

    def test_backtest_result_creation_and_immutability(self):
        """Test BacktestResult initialization and frozen immutability."""
        from src.trading.backtest import BacktestResult

        res = BacktestResult(
            run_id="run_001",
            strategy_id="ema_20_50",
            dataset_id="btcusdt_binance_perp_15m",
            initial_capital=10000.0,
            bars_processed=100,
            final_timestamp=self.now,
            signals=(self.signal,),
            orders=(self.order,),
            fills=(self.fill,),
            portfolio_history=(self.portfolio_state,),
            final_portfolio=self.portfolio_state,
        )

        self.assertEqual(res.run_id, "run_001")
        self.assertEqual(res.strategy_id, "ema_20_50")
        self.assertEqual(res.dataset_id, "btcusdt_binance_perp_15m")
        self.assertEqual(res.initial_capital, 10000.0)
        self.assertEqual(res.bars_processed, 100)
        self.assertEqual(len(res.signals), 1)
        self.assertEqual(len(res.orders), 1)
        self.assertEqual(len(res.fills), 1)
        self.assertEqual(len(res.portfolio_history), 1)
        self.assertEqual(res.closed_trades, ())

        # Test tuple immutability
        self.assertIsInstance(res.signals, tuple)
        self.assertIsInstance(res.fills, tuple)
        self.assertIsInstance(res.closed_trades, tuple)
        with self.assertRaises(AttributeError):
            res.bars_processed = 200

    def test_convenience_properties(self):
        """Test final_cash, final_equity, realized_pnl, and total_fees convenience properties."""
        from src.trading.backtest import BacktestResult

        res = BacktestResult(
            run_id="run_002",
            strategy_id="ema_20_50",
            dataset_id="btcusdt_15m",
            initial_capital=10000.0,
            bars_processed=50,
            final_timestamp=self.now,
            signals=(),
            orders=(),
            fills=(),
            portfolio_history=(),
            final_portfolio=self.portfolio_state,
        )

        self.assertEqual(res.final_cash, 10000.0)
        self.assertEqual(res.final_equity, 10000.0)
        self.assertEqual(res.realized_pnl, 0.0)
        self.assertEqual(res.total_fees, 8.0)


if __name__ == "__main__":
    unittest.main()
