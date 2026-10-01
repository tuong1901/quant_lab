"""
Execution & Backtest Engine Subsystem (`src/engine`).
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
from src.engine.order import OrderSide, OrderType, OrderStatus, Order
from src.engine.fill import Fill
from src.engine.result import ExecutionResult
from src.engine.fill_model import FillModel, OHLCFillModel, LowerTimeframeReplayFillModel
from src.engine.slippage import SlippageModel, FixedSlippageModel, VolatilitySlippageModel
from src.engine.fee import FeeModel, PercentageFeeModel
from src.engine.funding import PerpetualFundingModel
from src.engine.broker import Broker, HistoricalBroker
from src.engine.execution_engine import ExecutionEngine
from src.engine.state import BacktestState
from src.engine.backtest_result import BacktestResult
from src.engine.backtest_engine import BacktestEngine
from src.engine.simulator import run_trade_simulation
from src.engine.optimizer import run_optuna_study, objective_function, evaluate_plateau_champion

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
    "FillModel",
    "OHLCFillModel",
    "LowerTimeframeReplayFillModel",
    "SlippageModel",
    "FixedSlippageModel",
    "VolatilitySlippageModel",
    "FeeModel",
    "PercentageFeeModel",
    "PerpetualFundingModel",
    "Broker",
    "HistoricalBroker",
    "ExecutionEngine",
    "BacktestState",
    "BacktestResult",
    "BacktestEngine",
    "run_trade_simulation",
    "run_optuna_study",
    "objective_function",
    "evaluate_plateau_champion",
]
