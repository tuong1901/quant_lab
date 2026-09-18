"""
[PURPOSE]: Define immutable data model for a TimeWindow (warmup & execution bounds).
[DEPENDENCIES]: datetime, dataclasses.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class TimeWindow:
    """
    [PURPOSE]: Immutable container defining a specific time window for backtesting.
    [DEPENDENCIES]: datetime.
    [ARGS]:
        warmup_start — Start timestamp of warmup data period.
        execution_start — Start timestamp of active strategy execution period.
        execution_end — End timestamp of strategy execution period.
    [RETURNS]: TimeWindow instance.
    [SIDE EFFECTS]: Raises ValueError if time order invariants are violated.
    """
    warmup_start: datetime
    execution_start: datetime
    execution_end: datetime

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate time order invariants and timezone awareness.
        [DEPENDENCIES]: datetime.
        """
        # Ensure all datetimes are timezone-aware
        if self.warmup_start.tzinfo is None or self.execution_start.tzinfo is None or self.execution_end.tzinfo is None:
            raise ValueError("All TimeWindow datetimes must be timezone-aware (e.g. UTC).")

        # Validate time sequence invariant: warmup_start <= execution_start < execution_end
        if not (self.warmup_start <= self.execution_start < self.execution_end):
            raise ValueError(
                f"Invalid TimeWindow invariant: must satisfy warmup_start ({self.warmup_start}) "
                f"<= execution_start ({self.execution_start}) < execution_end ({self.execution_end})."
            )

    @property
    def warmup_duration(self):
        """
        [PURPOSE]: Return timedelta of warmup period.
        [RETURNS]: timedelta object.
        """
        return self.execution_start - self.warmup_start

    @property
    def execution_duration(self):
        """
        [PURPOSE]: Return timedelta of execution period.
        [RETURNS]: timedelta object.
        """
        return self.execution_end - self.execution_start

    @property
    def total_duration(self):
        """
        [PURPOSE]: Return timedelta of total window (warmup + execution).
        [RETURNS]: timedelta object.
        """
        return self.execution_end - self.warmup_start
