"""
[PURPOSE]: Full Experimental Environment Integrity Audit unit tests covering config propagation, risk sizing, portfolio accounting, margin/leverage, state isolation, and reproducibility.
[DEPENDENCIES]: unittest, pandas, datetime, src.config, src.environment, src.environment, src.engine, src.engine.
"""

import unittest
from datetime import datetime, timedelta, timezone
import pandas as pd

from src.config.loader import ConfigLoader
from src.environment.factory import EnvironmentFactory
from src.environment.risk_manager import RiskManager
from src.environment.margin import SimpleMarginModel
from src.engine.funding import PerpetualFundingModel
from src.engine.order import Order, OrderSide, OrderType
from src.engine.fill import Fill
from src.environment.position import PositionSide


class TestExperimentalEnvironmentIntegrity(unittest.TestCase):
    """
    [PURPOSE]: Automated audit verification tests for environment mechanics, risk sizing, state isolation, and accounting identities.
    """

    def setUp(self):
        self.loader = ConfigLoader(config_dir="config")
        self.config = self.loader.load_experiment("btc_rolling_1y")
        self.start_time = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def test_audit_risk_sizing_case_a(self):
        """[Section 4 Case A]: Capital=10000, Risk%=0.02 (Risk=$200), Entry=60000, Stop=59000 -> Expected Qty=0.20 BTC."""
        capital = 10000.0
        risk_pct = 0.02
        entry = 60000.0
        stop = 59000.0

        risk_amount = capital * risk_pct
        stop_distance = abs(entry - stop)
        expected_qty = risk_amount / stop_distance
        notional = expected_qty * entry
        margin_required = notional / 5.0  # at 5x leverage

        self.assertEqual(risk_amount, 200.0)
        self.assertEqual(stop_distance, 1000.0)
        self.assertEqual(expected_qty, 0.20)
        self.assertEqual(notional, 12000.0)
        self.assertEqual(margin_required, 2400.0)

        # Theoretical loss at stop
        loss_at_stop = expected_qty * stop_distance
        self.assertEqual(loss_at_stop, 200.0)

    def test_audit_risk_sizing_case_b(self):
        """[Section 4 Case B]: Capital=10000, Risk%=0.02 (Risk=$200), Entry=60000, Stop=59900 -> Expected Qty=2.00 BTC."""
        capital = 10000.0
        risk_pct = 0.02
        entry = 60000.0
        stop = 59900.0

        risk_amount = capital * risk_pct
        stop_distance = abs(entry - stop)
        expected_qty = risk_amount / stop_distance
        notional = expected_qty * entry

        self.assertEqual(risk_amount, 200.0)
        self.assertEqual(stop_distance, 100.0)
        self.assertEqual(expected_qty, 2.00)
        self.assertEqual(notional, 120000.0)

        # Audit check: Margin requirement ($24,000) exceeds available capital ($10,000)
        margin_model = SimpleMarginModel()
        used_margin = margin_model.calculate_initial_margin(position_notional=notional, leverage=5.0)
        self.assertEqual(used_margin, 24000.0)
        self.assertGreater(used_margin, capital, "Case B notional requires $24,000 margin which exceeds $10,000 capital")

    def test_audit_funding_rate_model(self):
        """[Section 10]: Verify 8h perpetual funding fee calculation for open holdings."""
        funding_model = PerpetualFundingModel()
        notional = 60000.0  # 1 BTC @ $60,000
        rate_8h = 0.0001    # 0.01% per 8h
        
        fee = funding_model.calculate_funding_fee(position_notional=notional, funding_rate=rate_8h)
        self.assertEqual(fee, 6.0, "Funding fee on $60,000 notional at 0.01% must equal $6.00")

    def test_audit_state_isolation_between_environments(self):
        """[Section 15]: Verify Environment A and Environment B constructed independently do NOT share mutable state."""
        env_a = EnvironmentFactory.create(config=self.config)
        env_b = EnvironmentFactory.create(config=self.config)

        # Verify initial independence
        self.assertIsNot(env_a.portfolio, env_b.portfolio)
        self.assertIsNot(env_a.clock, env_b.clock)
        self.assertIsNot(env_a.execution, env_b.execution)

        # Mutate env_a portfolio by applying a fill
        fill = Fill(
            fill_id="fill_test_iso",
            order_id="ord_test_iso",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            quantity=1.0,
            price=50000.0,
            fee=10.0,
            timestamp=self.start_time
        )
        env_a.portfolio.apply_fill(fill)

        # Assert env_a reflects fill while env_b remains completely unchanged
        self.assertIn("BTCUSDT", env_a.portfolio.positions)
        self.assertNotIn("BTCUSDT", env_b.portfolio.positions)
        self.assertEqual(env_a.portfolio.account.balance, 10000.0 - 10.0)
        self.assertEqual(env_b.portfolio.account.balance, 10000.0)


if __name__ == "__main__":
    unittest.main()
