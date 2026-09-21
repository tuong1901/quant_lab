"""
Strategy Subsystem (`src/strategies/`).

Defines Strategy Contract, StrategyContext, Signal, and reference strategy implementations.
"""

from src.strategies.exceptions import (
    StrategyError,
    InvalidSignalError,
    StrategyContextError,
)
from src.strategies.signal import SignalAction, Signal
from src.strategies.context import StrategyContext
from src.strategies.strategy import Strategy
from src.strategies.ema import EMAStrategy

__all__ = [
    "StrategyError",
    "InvalidSignalError",
    "StrategyContextError",
    "SignalAction",
    "Signal",
    "StrategyContext",
    "Strategy",
    "EMAStrategy",
]
