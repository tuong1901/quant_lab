"""
Backtest loop & orchestration exports (`src/engine/backtest/__init__.py`).
"""

from src.engine.backtest.state import BacktestState
from src.engine.backtest.backtest_result import BacktestResult
from src.engine.backtest.backtest_engine import BacktestEngine
from src.engine.backtest.simulator import run_trade_simulation
from src.engine.backtest.optimizer import (
    run_optuna_study,
    objective_function,
    evaluate_plateau_champion,
)

__all__ = [
    "BacktestState",
    "BacktestResult",
    "BacktestEngine",
    "run_trade_simulation",
    "run_optuna_study",
    "objective_function",
    "evaluate_plateau_champion",
]

