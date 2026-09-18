"""
Unit tests for schema and cross-config validation (`src/config/validation.py`).
"""

import unittest
from datetime import datetime, timezone

from src.market_data.market import Market
from src.market_data.timeframe import Timeframe
from src.market_data.dataset import StorageReference
from src.config.models import (
    SystemConfig,
    ClockConfig,
    ReproducibilityConfig,
    BoundaryConfig,
    DefaultEnvConfig,
    DatasetRefConfig,
    FillConfig,
    SlippageConfig,
    FeeConfig,
    FundingConfig,
    ExecutionConfig,
    AccountConfig,
    LeverageConfig,
    PositionConfig,
    RiskConfig,
    PortfolioConfig,
    ExperimentTimeConfig,
    ExperimentConfig,
)
from src.config.validation import validate_experiment_config
from src.config.exceptions import ConfigValidationError, ConfigCompatibilityError


class TestConfigValidation(unittest.TestCase):
    """
    [PURPOSE]: Verify cross-config compatibility checks (symbol mismatch, leverage limit violation).
    """

    def setUp(self):
        self.env = DefaultEnvConfig(
            name="default",
            system=SystemConfig(name="quant_lab", timezone="UTC"),
            clock=ClockConfig(mode="historical"),
            reproducibility=ReproducibilityConfig(seed=42),
            boundary=BoundaryConfig(policy="strict"),
        )
        self.market_btc = Market("binance", "BTCUSDT", "perpetual", "USDT")
        self.market_eth = Market("binance", "ETHUSDT", "perpetual", "USDT")
        self.storage_ref = StorageReference("local", "dummy.parquet")

        self.ds_btc_15m = DatasetRefConfig(
            name="btcusdt_15m",
            dataset_id="btcusdt_binance_perp_15m",
            version=1,
            market=self.market_btc,
            timeframe=Timeframe.M15,
            storage_reference=self.storage_ref,
        )

        self.ds_btc_1m = DatasetRefConfig(
            name="btcusdt_1m",
            dataset_id="btcusdt_binance_perp_1m",
            version=1,
            market=self.market_btc,
            timeframe=Timeframe.M1,
            storage_reference=self.storage_ref,
        )

        self.ds_eth_1m = DatasetRefConfig(
            name="ethusdt_1m",
            dataset_id="ethusdt_binance_perp_1m",
            version=1,
            market=self.market_eth,
            timeframe=Timeframe.M1,
            storage_reference=self.storage_ref,
        )

        self.exec_cfg = ExecutionConfig(
            name="default",
            fill=FillConfig(),
            slippage=SlippageConfig(),
            fee=FeeConfig(),
            funding=FundingConfig(),
        )

        self.port_cfg = PortfolioConfig(
            name="default",
            account=AccountConfig(),
            leverage=LeverageConfig(mode="fixed", value=5.0),
            position=PositionConfig(),
            risk=RiskConfig(max_leverage=5.0),
        )

        self.time_cfg = ExperimentTimeConfig(
            mode="fixed",
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2025, 1, 1, tzinfo=timezone.utc),
            resolved_anchor=datetime.now(timezone.utc),
        )

    def test_valid_experiment_config_passes_validation(self):
        """Test that compatible strategy and execution datasets pass validation."""
        exp_cfg = ExperimentConfig(
            name="valid_exp",
            environment=self.env,
            strategy_dataset=self.ds_btc_15m,
            execution_dataset=self.ds_btc_1m,
            execution=self.exec_cfg,
            portfolio=self.port_cfg,
            time=self.time_cfg,
        )
        # Should not raise any exception
        validate_experiment_config(exp_cfg)

    def test_symbol_mismatch_raises_compatibility_error(self):
        """Test that symbol mismatch between strategy and execution dataset raises ConfigCompatibilityError."""
        exp_cfg = ExperimentConfig(
            name="mismatched_exp",
            environment=self.env,
            strategy_dataset=self.ds_btc_15m,
            execution_dataset=self.ds_eth_1m,  # ETH instead of BTC
            execution=self.exec_cfg,
            portfolio=self.port_cfg,
            time=self.time_cfg,
        )
        with self.assertRaises(ConfigCompatibilityError):
            validate_experiment_config(exp_cfg)

    def test_leverage_exceeds_max_risk_raises_validation_error(self):
        """Test that configured leverage > max_leverage risk limit raises ConfigValidationError."""
        bad_port_cfg = PortfolioConfig(
            name="bad_leverage",
            account=AccountConfig(),
            leverage=LeverageConfig(mode="fixed", value=10.0),  # 10x leverage
            position=PositionConfig(),
            risk=RiskConfig(max_leverage=5.0),  # Max allowed 5x
        )
        exp_cfg = ExperimentConfig(
            name="high_leverage_exp",
            environment=self.env,
            strategy_dataset=self.ds_btc_15m,
            execution_dataset=self.ds_btc_1m,
            execution=self.exec_cfg,
            portfolio=bad_port_cfg,
            time=self.time_cfg,
        )
        with self.assertRaises(ConfigValidationError):
            validate_experiment_config(exp_cfg)


if __name__ == "__main__":
    unittest.main()
