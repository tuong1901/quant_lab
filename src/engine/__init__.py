"""
Engine package master SSOT exports (`src/engine/__init__.py`).
"""

from src.engine.exceptions import (
    EngineError,
    ExecutionError,
    InvalidOrderError,
    FillError,
    BacktestError,
    BacktestExecutionError,
    InvalidSimulationStateError,
)
from src.engine.execution import (
    OrderSide,
    OrderType,
    OrderStatus,
    Order,
    Fill,
    ExecutionResult,
    Broker,
    HistoricalBroker,
    ExecutionEngine,
)
from src.engine.models import (
    FillModel,
    OHLCFillModel,
    LowerTimeframeReplayFillModel,
    SlippageModel,
    FixedSlippageModel,
    VolatilitySlippageModel,
    FeeModel,
    PercentageFeeModel,
    PerpetualFundingModel,
)
from src.engine.backtest import (
    BacktestState,
    BacktestResult,
    BacktestEngine,
    run_trade_simulation,
    run_optuna_study,
    objective_function,
    evaluate_plateau_champion,
)

__all__ = [
    "EngineError",
    "ExecutionError",
    "InvalidOrderError",
    "FillError",
    "BacktestError",
    "BacktestExecutionError",
    "InvalidSimulationStateError",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "Order",
    "Fill",
    "ExecutionResult",
    "Broker",
    "HistoricalBroker",
    "ExecutionEngine",
    "FillModel",
    "OHLCFillModel",
    "LowerTimeframeReplayFillModel",
    "SlippageModel",
    "FixedSlippageModel",
    "VolatilitySlippageModel",
    "FeeModel",
    "PercentageFeeModel",
    "PerpetualFundingModel",
    "BacktestState",
    "BacktestResult",
    "BacktestEngine",
    "run_trade_simulation",
    "run_optuna_study",
    "objective_function",
    "evaluate_plateau_champion",
]
