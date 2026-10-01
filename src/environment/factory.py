"""
EnvironmentFactory runtime composition engine for building Environment instances.
"""

from typing import Optional, Any

from src.core.clock import HistoricalClock
from src.data.loader import DatasetLoader
from src.engine.execution_engine import ExecutionEngine
from src.environment.portfolio import Portfolio
from src.config.models import ExperimentConfig
from src.environment.environment import Environment
from src.environment.registry import Registry
from src.environment.exceptions import EnvironmentConstructionError


class EnvironmentFactory:
    """
    [PURPOSE]: Factory service responsible for constructing clean Environment runtime instances.
    [DEPENDENCIES]: Environment, Registry, HistoricalClock, DatasetLoader, ExecutionEngine, Portfolio, ExperimentConfig.
    [ARGS]: None (stateless factory).
    [RETURNS]: Environment instance via create() method.
    [SIDE EFFECTS]: Instantiates dependency instances if not explicitly provided.
    """

    @classmethod
    def create(
        cls,
        config: ExperimentConfig,
        clock: Optional[Any] = None,
        market_data: Optional[Any] = None,
        execution_engine: Optional[Any] = None,
        portfolio: Optional[Any] = None,
    ) -> Environment:
        """
        [PURPOSE]: Assemble and wire an Environment instance from typed ExperimentConfig or injected dependencies.
        [DEPENDENCIES]: Instantiates default HistoricalClock, DatasetLoader, ExecutionEngine, and Portfolio if omitted.
        [ARGS]:
            config — Typed ExperimentConfig root object (required).
            clock — Optional pre-constructed clock override.
            market_data — Optional pre-constructed market_data loader override.
            execution_engine — Optional pre-constructed execution engine override.
            portfolio — Optional pre-constructed portfolio override.
        [RETURNS]: Fully constructed Environment instance.
        [SIDE EFFECTS]: Raises EnvironmentConstructionError if config is None.
        """
        if config is None:
            raise EnvironmentConstructionError("Configuration parameter 'config' cannot be None.")

        if clock is None:
            start_time = getattr(getattr(config, "time", None), "start", None)
            if start_time is not None:
                clock = HistoricalClock(start_time=start_time)
            else:
                clock = HistoricalClock()

        if market_data is None:
            market_data = DatasetLoader()

        if execution_engine is None:
            execution_engine = ExecutionEngine()

        if portfolio is None:
            initial_cap = 10000.0
            leverage = 1.0
            if hasattr(config, "portfolio") and config.portfolio is not None:
                if hasattr(config.portfolio, "account") and config.portfolio.account is not None:
                    initial_cap = getattr(config.portfolio.account, "initial_capital", 10000.0)
                if hasattr(config.portfolio, "leverage") and config.portfolio.leverage is not None:
                    leverage = getattr(config.portfolio.leverage, "value", 1.0)
            portfolio = Portfolio(initial_capital=initial_cap, leverage=leverage)

        registry = Registry()

        return Environment(
            clock=clock,
            market_data=market_data,
            execution=execution_engine,
            portfolio=portfolio,
            config=config,
            registry=registry,
        )
