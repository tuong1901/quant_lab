"""
Clock Abstraction & Implementations (`src/core/clock.py`).

Provides temporal source contract (now()) and deterministic HistoricalClock for simulation.
"""

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from src.core.exceptions import QuantSystemError
from src.core.types import validate_utc_timestamp


@runtime_checkable
class Clock(Protocol):
    """
    [PURPOSE]: Protocol defining contract for reading system or simulated time.
    [DEPENDENCIES]: Used by Strategy, Execution, and Backtest engines.
    """
    def now(self) -> datetime:
        """Return current timestamp (UTC aware)."""
        ...


class HistoricalClock:
    """
    [PURPOSE]: Simulated clock for backtest and historical replay.
    [DEPENDENCIES]: Uses validate_utc_timestamp and QuantSystemError.
    [ARGS]: start_time — Initial simulated datetime (must be UTC aware).
    [RETURNS]: HistoricalClock instance.
    [SIDE EFFECTS]: Maintains internal simulated timestamp.
    """

    def __init__(self, start_time: datetime) -> None:
        """
        [PURPOSE]: Initialize HistoricalClock with a UTC starting time.
        """
        self._current_time = validate_utc_timestamp(start_time)

    def now(self) -> datetime:
        """
        [PURPOSE]: Return current simulated timestamp.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: datetime UTC.
        [SIDE EFFECTS]: None.
        """
        return self._current_time

    def set(self, dt: datetime) -> None:
        """
        [PURPOSE]: Explicitly set current simulated timestamp.
        [DEPENDENCIES]: Validates UTC awareness.
        [ARGS]: dt — New simulated datetime.
        [RETURNS]: None.
        [SIDE EFFECTS]: Updates internal simulated timestamp.
        """
        self._current_time = validate_utc_timestamp(dt)

    def advance_to(self, dt: datetime) -> None:
        """
        [PURPOSE]: Advance simulated clock forward to new timestamp.
        [DEPENDENCIES]: Validates UTC awareness and dt >= current_time invariant.
        [ARGS]: dt — New simulated datetime (must be >= current_time).
        [RETURNS]: None.
        [SIDE EFFECTS]: Updates internal simulated timestamp.
        """
        target_dt = validate_utc_timestamp(dt)
        if target_dt < self._current_time:
            raise QuantSystemError(
                f"Cannot advance HistoricalClock backward in time: target {target_dt} < current {self._current_time}"
            )
        self._current_time = target_dt


class RealtimeClock:
    """
    [PURPOSE]: Wall-clock provider for paper and live trading.
    [DEPENDENCIES]: Uses stdlib datetime.now(timezone.utc).
    [ARGS]: None.
    [RETURNS]: RealtimeClock instance.
    [SIDE EFFECTS]: Reads system clock.
    """

    def now(self) -> datetime:
        """
        [PURPOSE]: Return current real-world UTC timestamp.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: datetime UTC.
        [SIDE EFFECTS]: None.
        """
        return datetime.now(timezone.utc)
