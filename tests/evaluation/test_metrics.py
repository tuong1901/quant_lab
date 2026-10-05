"""
Unit tests for BasicMetrics performance calculator (`src/evaluation/metrics.py`).
"""

import unittest
from datetime import datetime, timezone

from src.strategies.signal import Signal, SignalAction
from src.trading.execution.order import Order, OrderSide, OrderType
from src.trading.execution.fill import Fill
from src.trading.portfolio.portfolio import PortfolioState
from src.trading.backtest import BacktestResult


class TestBasicMetrics(unittest.TestCase):
    """
    [PURPOSE]: Verify BasicMetrics performance calculations, trade count, win rate, equity curve, and immutability.
    """

    def setUp(self):
        self.t1 = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.t2 = datetime(2024, 1, 1, 12, 15, tzinfo=timezone.utc)
        self.t3 = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)

        # Snapshot 1: Start $10,000
        p1 = PortfolioState(
            timestamp=self.t1,
            balance=10000.0,
            equity=10000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            fees_paid=0.0,
            funding_paid=0.0,
            used_margin=0.0,
            available_margin=10000.0,
        )
        # Snapshot 2: Trade 1 Win (Realized +$500, Fee $10)
        p2 = PortfolioState(
            timestamp=self.t2,
            balance=10490.0,
            equity=10490.0,
            realized_pnl=500.0,
            unrealized_pnl=0.0,
            fees_paid=10.0,
            funding_paid=0.0,
            used_margin=0.0,
            available_margin=10490.0,
        )
        # Snapshot 3: Trade 2 Loss (Realized +$300 net -> delta -$200, Fee $20 total)
        p3 = PortfolioState(
            timestamp=self.t3,
            balance=10280.0,
            equity=10280.0,
            realized_pnl=300.0,
            unrealized_pnl=0.0,
            fees_paid=20.0,
            funding_paid=0.0,
            used_margin=0.0,
            available_margin=10280.0,
        )

        self.sample_result = BacktestResult(
            run_id="run_test",
            strategy_id="ema_20_50",
            dataset_id="btcusdt_15m",
            initial_capital=10000.0,
            bars_processed=3,
            final_timestamp=self.t3,
            signals=(),
            orders=(),
            fills=(),
            portfolio_history=(p1, p2, p3),
            final_portfolio=p3,
        )

    def test_profitable_metrics_calculation(self):
        """Test net_pnl, return_pct, trade_count, win_rate on profitable result."""
        from src.evaluation.metrics import calculate_basic_metrics, BasicMetrics

        metrics = calculate_basic_metrics(self.sample_result)

        self.assertIsInstance(metrics, BasicMetrics)
        self.assertEqual(metrics.initial_capital, 10000.0)
        self.assertEqual(metrics.final_equity, 10280.0)
        self.assertAlmostEqual(metrics.net_pnl, 280.0)
        self.assertAlmostEqual(metrics.return_pct, 2.8)
        self.assertEqual(metrics.realized_pnl, 300.0)
        self.assertEqual(metrics.total_fees, 20.0)

        # 2 completed trades: Trade 1 delta +$500 (Win), Trade 2 delta -$200 (Loss)
        self.assertEqual(metrics.trade_count, 2)
        self.assertAlmostEqual(metrics.win_rate, 50.0)

    def test_equity_curve_and_immutability(self):
        """Test equity_curve chronological tuple generation and frozen immutability."""
        from src.evaluation.metrics import calculate_basic_metrics

        metrics = calculate_basic_metrics(self.sample_result)

        self.assertIsInstance(metrics.equity_curve, tuple)
        self.assertEqual(len(metrics.equity_curve), 3)
        self.assertEqual(metrics.equity_curve[0], (self.t1, 10000.0))
        self.assertEqual(metrics.equity_curve[1], (self.t2, 10490.0))
        self.assertEqual(metrics.equity_curve[2], (self.t3, 10280.0))

        with self.assertRaises(AttributeError):
            metrics.net_pnl = 500.0

    def test_invalid_initial_capital_raises_error(self):
        """Test that initial_capital <= 0 raises InvalidEvaluationError."""
        from src.evaluation.metrics import calculate_basic_metrics
        from src.evaluation.exceptions import InvalidEvaluationError

        bad_result = BacktestResult(
            run_id="run_zero",
            strategy_id="ema_20_50",
            dataset_id="btcusdt_15m",
            initial_capital=0.0,
            bars_processed=0,
            final_timestamp=None,
            signals=(),
            orders=(),
            fills=(),
            portfolio_history=(),
            final_portfolio=None,
        )

        with self.assertRaises(InvalidEvaluationError):
            calculate_basic_metrics(bad_result)


if __name__ == "__main__":
    unittest.main()
