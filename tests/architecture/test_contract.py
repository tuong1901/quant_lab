"""
[PURPOSE]: Architecture Contract Integration Test proving end-to-end domain connection (Market Data -> Strategy -> Signal -> Backtest -> Order -> Execution -> Fill -> Portfolio -> BacktestResult -> Evaluation -> BasicMetrics).
[DEPENDENCIES]: unittest, pandas, datetime, src.config, src.environment, src.strategies, src.engine, src.evaluation.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.runtime.factory import EnvironmentFactory
from src.strategies.ema import EMAStrategy
from src.strategies.signal import Signal
from src.engine.execution.order import Order
from src.engine.execution.fill import Fill
from src.environment.accounting.portfolio_state import PortfolioState
from src.engine.backtest.backtest_engine import BacktestEngine
from src.engine.backtest.backtest_result import BacktestResult
from src.evaluation.metrics import BasicMetrics, calculate_basic_metrics


class TestArchitectureContractIntegration(unittest.TestCase):
    """
    [PURPOSE]: Enforce end-to-end domain boundary contract connections across all system layers.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_full_architecture_contract_pipeline(self):
        """[Architecture Contract]: Verify 10-layer contract flow from Market Data to BasicMetrics."""
        # 1. Market Data
        data = []
        for i in range(10):
            ts = self.start_time + timedelta(minutes=15 * i)
            p = 50000.0 + i * 10.0
            data.append({
                "timestamp": ts,
                "open": p,
                "high": p + 5.0,
                "low": p - 5.0,
                "close": p,
                "volume": 10.0,
                "ema20": p + 1.0,
                "ema50": p,
            })
        df = pd.DataFrame(data)

        # 2. Strategy & Environment Composition
        env = EnvironmentFactory.create(config=self.config)
        strat = EMAStrategy(fast_period=20, slow_period=50)

        # 3. Backtest Engine (Orchestration)
        engine = BacktestEngine(environment=env, strategy=strat)
        result = engine.run(df=df)

        # Verify BacktestResult Contract
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.bars_processed, 10)
        self.assertGreater(len(result.signals), 0)
        self.assertIsInstance(result.signals[0], Signal)

        if len(result.orders) > 0:
            self.assertIsInstance(result.orders[0], Order)
        if len(result.fills) > 0:
            self.assertIsInstance(result.fills[0], Fill)
        if len(result.portfolio_history) > 0:
            self.assertIsInstance(result.portfolio_history[0], PortfolioState)

        # 4. Evaluation Engine (Metrics Output)
        metrics = calculate_basic_metrics(result)
        self.assertIsInstance(metrics, BasicMetrics)
        self.assertEqual(metrics.initial_capital, 10000.0)
        self.assertIsInstance(metrics.equity_curve, tuple)


if __name__ == "__main__":
    unittest.main()
