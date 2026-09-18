"""
Config Validation Engine (`src/config/validation.py`).

Performs schema validation and cross-config compatibility checks.
"""

from src.config.models import ExperimentConfig
from src.config.exceptions import ConfigValidationError, ConfigCompatibilityError


def validate_experiment_config(exp_config: ExperimentConfig) -> None:
    """
    [PURPOSE]: Perform strict cross-config compatibility checks on a resolved ExperimentConfig.
    [DEPENDENCIES]: Raises ConfigValidationError or ConfigCompatibilityError on failure.
    [ARGS]: exp_config — ExperimentConfig instance.
    [RETURNS]: None.
    [SIDE EFFECTS]: None (pure validation).
    """
    if not isinstance(exp_config, ExperimentConfig):
        raise ConfigValidationError(f"Expected ExperimentConfig instance, got {type(exp_config)}")

    s_ds = exp_config.strategy_dataset
    e_ds = exp_config.execution_dataset

    # 1. Cross-config Validation: Market identity match between strategy dataset and execution dataset
    if s_ds.market.venue != e_ds.market.venue:
        raise ConfigCompatibilityError(
            f"Strategy dataset venue '{s_ds.market.venue}' does not match execution dataset venue '{e_ds.market.venue}'"
        )

    if s_ds.market.symbol != e_ds.market.symbol:
        raise ConfigCompatibilityError(
            f"Strategy dataset symbol '{s_ds.market.symbol}' does not match execution dataset symbol '{e_ds.market.symbol}'"
        )

    if s_ds.market.market_type != e_ds.market.market_type:
        raise ConfigCompatibilityError(
            f"Strategy dataset market_type '{s_ds.market.market_type}' does not match execution dataset market_type '{e_ds.market.market_type}'"
        )

    if s_ds.market.quote_currency != e_ds.market.quote_currency:
        raise ConfigCompatibilityError(
            f"Strategy dataset quote_currency '{s_ds.market.quote_currency}' does not match execution dataset quote_currency '{e_ds.market.quote_currency}'"
        )

    # 2. Validation of time mode requirements
    t_cfg = exp_config.time
    if t_cfg.mode == "rolling":
        if not t_cfg.window_duration:
            raise ConfigValidationError("Rolling time mode requires 'window.duration' setting.")
        if not t_cfg.step_duration:
            raise ConfigValidationError("Rolling time mode requires 'step.duration' setting.")

    # 3. Cross-config Validation: Leverage vs Risk limit check
    if exp_config.portfolio.leverage.value > exp_config.portfolio.risk.max_leverage:
        raise ConfigValidationError(
            f"Configured leverage ({exp_config.portfolio.leverage.value}) exceeds risk max_leverage limit ({exp_config.portfolio.risk.max_leverage})"
        )
