"""
[PURPOSE]: Planner engine that resolves time configurations, calculates windows, checks dataset boundaries, and generates ExperimentRuns.
[DEPENDENCIES]: datetime, dataclasses, typing, src.experiments.config, src.experiments.window, src.experiments.run.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Union
from src.experiments.config import TimeConfig, Duration, DurationUnit
from src.experiments.window import TimeWindow
from src.experiments.run import ExperimentRun

class PlanningError(Exception):
    """Custom exception raised when planning calculations or boundary checks fail."""
    pass

@dataclass(frozen=True)
class DatasetRange:
    """
    [PURPOSE]: Abstract boundary representation of available dataset start and end timestamps.
    [DEPENDENCIES]: datetime.
    [ARGS]:
        start — Earliest available timestamp in dataset.
        end — Latest available timestamp in dataset.
        timeframe_minutes — Timeframe bar length in minutes (default 15 for 15m nến).
    [RETURNS]: DatasetRange instance.
    [SIDE EFFECTS]: Raises ValueError if start >= end or missing timezone.
    """
    start: datetime
    end: datetime
    timeframe_minutes: int = 15

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("DatasetRange start and end must be timezone-aware.")
        if self.start >= self.end:
            raise ValueError(f"DatasetRange start ({self.start}) must be before end ({self.end}).")

def _add_duration(dt: datetime, duration: Duration, timeframe_minutes: int) -> datetime:
    """
    [PURPOSE]: Add a Duration object to a datetime instance.
    [DEPENDENCIES]: datetime, timedelta, Duration, DurationUnit.
    """
    unit = duration.unit
    val = duration.value

    if unit == DurationUnit.BARS:
        return dt + timedelta(minutes=val * timeframe_minutes)
    elif unit == DurationUnit.HOURS:
        return dt + timedelta(hours=val)
    elif unit == DurationUnit.DAYS:
        return dt + timedelta(days=val)
    elif unit == DurationUnit.MONTHS:
        return dt + timedelta(days=30 * val)
    elif unit == DurationUnit.YEARS:
        return dt + timedelta(days=365 * val)
    else:
        raise PlanningError(f"Unsupported duration unit '{unit}'.")

def _subtract_duration(dt: datetime, duration: Duration, timeframe_minutes: int) -> datetime:
    """
    [PURPOSE]: Subtract a Duration object from a datetime instance.
    [DEPENDENCIES]: datetime, timedelta, Duration, DurationUnit.
    """
    unit = duration.unit
    val = duration.value

    if unit == DurationUnit.BARS:
        return dt - timedelta(minutes=val * timeframe_minutes)
    elif unit == DurationUnit.HOURS:
        return dt - timedelta(hours=val)
    elif unit == DurationUnit.DAYS:
        return dt - timedelta(days=val)
    elif unit == DurationUnit.MONTHS:
        return dt - timedelta(days=30 * val)
    elif unit == DurationUnit.YEARS:
        return dt - timedelta(days=365 * val)
    else:
        raise PlanningError(f"Unsupported duration unit '{unit}'.")

def _parse_datetime_arg(val_str: Union[str, datetime], now_dt: datetime) -> datetime:
    """
    [PURPOSE]: Resolve string datetime or 'now' to timezone-aware UTC datetime.
    [DEPENDENCIES]: datetime, timezone.
    """
    if isinstance(val_str, datetime):
        if val_str.tzinfo is None:
            return val_str.replace(tzinfo=timezone.utc)
        return val_str.astimezone(timezone.utc)

    s = str(val_str).strip()
    if s.lower() == "now":
        return now_dt

    try:
        # Try ISO format or standard YYYY-MM-DD HH:MM:SS / YYYY-MM-DD
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        raise PlanningError(f"Cannot parse datetime string '{val_str}'. Expected format YYYY-MM-DD or ISO string.")

class TimePlanner:
    """
    [PURPOSE]: Brain engine that takes TimeConfig + DatasetRange and generates ExperimentRun list.
    [DEPENDENCIES]: TimeConfig, DatasetRange, ExperimentRun, TimeWindow, PlanningError.
    """

    def plan(
        self,
        config: TimeConfig,
        dataset_range: DatasetRange,
        now: Optional[datetime] = None,
        run_id_prefix: str = "run"
    ) -> List[ExperimentRun]:
        """
        [PURPOSE]: Generate list of ExperimentRun instances based on time config and dataset bounds.
        [DEPENDENCIES]: DatasetRange, TimeConfig, ExperimentRun, PlanningError.
        [ARGS]:
            config — TimeConfig object defining desired experiment timings.
            dataset_range — DatasetRange object holding dataset start and end bounds.
            now — Optional explicit datetime for freezing 'now' deterministically.
            run_id_prefix — String prefix for generated run_ids.
        [RETURNS]: List of ExperimentRun objects.
        [SIDE EFFECTS]: Raises PlanningError if requested bounds exceed dataset or configuration is invalid.
        """
        # Resolve 'now' deterministically
        if now is not None:
            if now.tzinfo is None:
                now_dt = now.replace(tzinfo=timezone.utc)
            else:
                now_dt = now.astimezone(timezone.utc)
        else:
            now_dt = datetime.now(timezone.utc)

        # Resolve anchor
        if config.anchor.lower() == "now":
            resolved_anchor = now_dt
        else:
            resolved_anchor = _parse_datetime_arg(config.anchor, now_dt)

        # Resolve range start and end
        range_start = _parse_datetime_arg(config.range_start, resolved_anchor)
        range_end = _parse_datetime_arg(config.range_end, resolved_anchor)

        if range_start >= range_end:
            raise PlanningError(
                f"Resolved range_start ({range_start}) must be before range_end ({range_end})."
            )

        # Generate execution windows based on mode
        raw_windows = []  # List of (exec_start, exec_end)
        tf_mins = dataset_range.timeframe_minutes

        if config.mode == "fixed":
            # Fixed mode: single window from range_start to range_end or range_start + window_duration
            exec_end = _add_duration(range_start, config.window_duration, tf_mins)
            if exec_end > range_end:
                exec_end = range_end
            raw_windows.append((range_start, exec_end))

        elif config.mode == "rolling":
            curr_start = range_start
            curr_end = _add_duration(curr_start, config.window_duration, tf_mins)
            while curr_end <= range_end:
                raw_windows.append((curr_start, curr_end))
                curr_start = _add_duration(curr_start, config.step_duration, tf_mins)
                curr_end = _add_duration(curr_start, config.window_duration, tf_mins)

        elif config.mode == "expanding":
            step_idx = 0
            curr_start = range_start
            while True:
                added_step = Duration(config.step_duration.value * step_idx, config.step_duration.unit) if step_idx > 0 else None
                base_end = _add_duration(curr_start, config.window_duration, tf_mins)
                curr_end = _add_duration(base_end, added_step, tf_mins) if added_step else base_end
                if curr_end > range_end:
                    break
                raw_windows.append((curr_start, curr_end))
                step_idx += 1

        if not raw_windows:
            raise PlanningError("No execution windows could be generated within the specified range.")

        # Compute warmup and construct ExperimentRun list
        runs = []
        for idx, (exec_start, exec_end) in enumerate(raw_windows, start=1):
            if config.warmup_duration:
                warmup_start = _subtract_duration(exec_start, config.warmup_duration, tf_mins)
            else:
                warmup_start = exec_start

            # Check dataset boundary limits
            if warmup_start < dataset_range.start or exec_end > dataset_range.end:
                raise PlanningError(
                    f"Requested window [warmup={warmup_start}, end={exec_end}] exceeds "
                    f"available dataset bounds [{dataset_range.start} -> {dataset_range.end}]."
                )

            time_window = TimeWindow(
                warmup_start=warmup_start,
                execution_start=exec_start,
                execution_end=exec_end
            )

            run_id = f"{run_id_prefix}_{idx:03d}"
            runs.append(ExperimentRun(run_id=run_id, window=time_window, seed=42))

        return runs
