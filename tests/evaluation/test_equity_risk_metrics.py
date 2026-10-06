"""Golden tests for equity-curve performance and risk evaluation."""

from datetime import datetime, timedelta, timezone
import math
import unittest

from src.data.timeframe import Timeframe
from src.evaluation.exceptions import InvalidEvaluationError
from src.evaluation.metrics import calculate_equity_risk_metrics, periods_per_year


START_TIME = datetime(2024, 1, 1, tzinfo=timezone.utc)


def make_curve(values, step: timedelta = timedelta(days=1)):
    """
    [PURPOSE]: Create a deterministic UTC equity curve for evaluation tests.
    [DEPENDENCIES]: Used only in this module's golden metric tests.
    [ARGS]: values — ordered equity values; step — spacing between snapshots.
    [RETURNS]: Tuple-like list of timestamp and equity pairs.
    [SIDE EFFECTS]: None.
    """
    return [(START_TIME + index * step, value) for index, value in enumerate(values)]


class TestEquityRiskMetrics(unittest.TestCase):
    """Verify P0 performance and risk metric formulas plus undefined-value policy."""

    def test_periods_per_year_are_timeframe_aware_for_crypto(self):
        self.assertEqual(periods_per_year(Timeframe.M15), 35040)
        self.assertEqual(periods_per_year(Timeframe.H1), 8760)
        self.assertEqual(periods_per_year(Timeframe.H4), 2190)
        self.assertEqual(periods_per_year(Timeframe.D1), 365)

    def test_net_pnl_return_and_cagr(self):
        metrics = calculate_equity_risk_metrics(
            make_curve([10000.0, 12100.0], step=timedelta(days=730)), Timeframe.D1
        )

        self.assertEqual(metrics.net_pnl, 2100.0)
        self.assertAlmostEqual(metrics.return_pct, 21.0)
        self.assertAlmostEqual(metrics.cagr, 0.10)

    def test_loss_return_is_negative(self):
        metrics = calculate_equity_risk_metrics(
            make_curve([10000.0, 8000.0], step=timedelta(days=365)), Timeframe.D1
        )

        self.assertEqual(metrics.net_pnl, -2000.0)
        self.assertAlmostEqual(metrics.return_pct, -20.0)
        self.assertAlmostEqual(metrics.cagr, -0.20)

    def test_max_drawdown_and_duration(self):
        metrics = calculate_equity_risk_metrics(
            make_curve([100.0, 120.0, 110.0, 90.0, 100.0, 130.0]), Timeframe.D1
        )

        self.assertEqual(metrics.max_drawdown, 30.0)
        self.assertEqual(metrics.max_drawdown_pct, 0.25)
        self.assertEqual(metrics.max_drawdown_duration_bars, 3)

    def test_monotonic_equity_has_zero_drawdown_and_undefined_calmar(self):
        metrics = calculate_equity_risk_metrics(make_curve([100.0, 110.0, 120.0]), Timeframe.D1)

        self.assertEqual(metrics.max_drawdown, 0.0)
        self.assertEqual(metrics.max_drawdown_pct, 0.0)
        self.assertIsNone(metrics.calmar_ratio)

    def test_sharpe_uses_timeframe_annualization_and_risk_free_rate(self):
        curve = make_curve([100.0, 101.0, 104.03])
        base = calculate_equity_risk_metrics(curve, Timeframe.M15)
        with_risk_free = calculate_equity_risk_metrics(curve, Timeframe.M15, risk_free_rate=0.10)

        self.assertAlmostEqual(base.sharpe_ratio, 2.0 * math.sqrt(35040))
        self.assertLess(with_risk_free.sharpe_ratio, base.sharpe_ratio)

    def test_sortino_uses_only_downside_returns(self):
        metrics = calculate_equity_risk_metrics(make_curve([100.0, 102.0, 100.98]), Timeframe.D1)
        expected = ((0.02 - 0.01) / 2.0) / math.sqrt((0.01 ** 2) / 2.0) * math.sqrt(365)

        self.assertAlmostEqual(metrics.sortino_ratio, expected)

    def test_zero_volatility_and_zero_downside_return_none(self):
        metrics = calculate_equity_risk_metrics(make_curve([100.0, 100.0, 100.0]), Timeframe.D1)

        self.assertEqual(metrics.annualized_volatility, 0.0)
        self.assertIsNone(metrics.sharpe_ratio)
        self.assertIsNone(metrics.sortino_ratio)

    def test_calmar_uses_cagr_divided_by_drawdown_magnitude(self):
        metrics = calculate_equity_risk_metrics(
            make_curve([10000.0, 12000.0, 10800.0, 12100.0], step=timedelta(days=730 // 3)),
            Timeframe.D1,
        )

        self.assertAlmostEqual(metrics.max_drawdown_pct, 0.10)
        self.assertAlmostEqual(metrics.calmar_ratio, metrics.cagr / 0.10)

    def test_invalid_equity_curve_inputs_raise_explicitly(self):
        with self.assertRaises(InvalidEvaluationError):
            calculate_equity_risk_metrics([], Timeframe.D1)
        with self.assertRaises(InvalidEvaluationError):
            calculate_equity_risk_metrics(make_curve([100.0, 0.0]), Timeframe.D1)
        with self.assertRaises(InvalidEvaluationError):
            calculate_equity_risk_metrics(
                [(START_TIME, 100.0), (START_TIME, 110.0)], Timeframe.D1
            )
        with self.assertRaises(InvalidEvaluationError):
            calculate_equity_risk_metrics(make_curve([100.0, 110.0]), Timeframe.D1, risk_free_rate=-1.0)
