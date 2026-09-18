"""
[PURPOSE]: Configuration parser and validator for Time & Experiment settings.
[DEPENDENCIES]: yaml, dataclasses, enum, re, typing.
"""

import re
import yaml
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union

class ConfigError(Exception):
    """Custom exception raised when configuration validation fails."""
    pass

class DurationUnit(Enum):
    YEARS = "y"
    MONTHS = "mo"
    DAYS = "d"
    HOURS = "h"
    BARS = "bars"

@dataclass(frozen=True)
class Duration:
    """
    [PURPOSE]: Immutable duration representation (value + unit).
    [DEPENDENCIES]: DurationUnit.
    """
    value: int
    unit: DurationUnit

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ConfigError(f"Duration value must be positive, got {self.value}.")

def parse_duration(duration_str: str) -> Duration:
    """
    [PURPOSE]: Parse string duration (e.g. '1y', '1mo', '30d', '24h', '200bars') into Duration object.
    [DEPENDENCIES]: re, Duration, DurationUnit, ConfigError.
    [ARGS]: duration_str — String representation of duration.
    [RETURNS]: Duration object.
    [SIDE EFFECTS]: Raises ConfigError on invalid format.
    """
    if not isinstance(duration_str, str):
        raise ConfigError(f"Duration must be a string, got {type(duration_str).__name__}.")

    duration_str = duration_str.strip()
    match = re.match(r"^(\d+)\s*(y|mo|d|h|bars)$", duration_str, re.IGNORECASE)
    if not match:
        raise ConfigError(
            f"Invalid duration string '{duration_str}'. Must be formatted like '1y', '1mo', '30d', '24h', or '200bars'."
        )

    val = int(match.group(1))
    unit_str = match.group(2).lower()

    for unit_enum in DurationUnit:
        if unit_enum.value == unit_str:
            return Duration(value=val, unit=unit_enum)

    raise ConfigError(f"Unknown duration unit '{unit_str}'.")

@dataclass(frozen=True)
class TimeConfig:
    """
    [PURPOSE]: Immutable user configuration for experiment timing.
    [DEPENDENCIES]: Duration, ConfigError.
    """
    mode: str
    range_start: str
    range_end: str
    anchor: str
    window_duration: Duration
    step_duration: Optional[Duration] = None
    warmup_duration: Optional[Duration] = None
    timezone: str = "UTC"
    freeze_anchor: bool = True

    def __post_init__(self) -> None:
        valid_modes = {"fixed", "rolling", "expanding"}
        if self.mode not in valid_modes:
            raise ConfigError(f"Invalid mode '{self.mode}'. Must be one of {valid_modes}.")

        if self.mode in {"rolling", "expanding"} and self.step_duration is None:
            raise ConfigError(f"Mode '{self.mode}' requires a step duration configuration.")

def parse_time_config(raw_dict: Dict[str, Any]) -> TimeConfig:
    """
    [PURPOSE]: Parse dictionary (loaded from YAML) into validated TimeConfig object.
    [DEPENDENCIES]: TimeConfig, parse_duration, ConfigError.
    [ARGS]: raw_dict — Dictionary containing configuration values.
    [RETURNS]: TimeConfig instance.
    [SIDE EFFECTS]: Raises ConfigError if parsing or validation fails.
    """
    if "time" in raw_dict:
        raw_dict = raw_dict["time"]

    required_fields = ["mode", "range", "window"]
    for field in required_fields:
        if field not in raw_dict:
            raise ConfigError(f"Missing required configuration field '{field}'.")

    mode = str(raw_dict["mode"]).lower()
    anchor = str(raw_dict.get("anchor", "now"))

    range_dict = raw_dict.get("range", {})
    if not isinstance(range_dict, dict) or "start" not in range_dict or "end" not in range_dict:
        raise ConfigError("Range section must contain 'start' and 'end' fields.")

    range_start = str(range_dict["start"])
    range_end = str(range_dict["end"])

    window_dict = raw_dict.get("window", {})
    if not isinstance(window_dict, dict) or "duration" not in window_dict:
        raise ConfigError("Window section must contain 'duration' field.")
    window_dur = parse_duration(str(window_dict["duration"]))

    step_dur = None
    if "step" in raw_dict and raw_dict["step"] is not None:
        step_dict = raw_dict["step"]
        if isinstance(step_dict, dict) and "duration" in step_dict:
            step_dur = parse_duration(str(step_dict["duration"]))

    warmup_dur = None
    if "warmup" in raw_dict and raw_dict["warmup"] is not None:
        warmup_dict = raw_dict["warmup"]
        if isinstance(warmup_dict, dict) and "duration" in warmup_dict:
            warmup_dur = parse_duration(str(warmup_dict["duration"]))

    tz = str(raw_dict.get("timezone", "UTC"))

    repro_dict = raw_dict.get("reproducibility", {})
    freeze_anchor = True
    if isinstance(repro_dict, dict):
        freeze_anchor = bool(repro_dict.get("freeze_anchor", True))

    return TimeConfig(
        mode=mode,
        range_start=range_start,
        range_end=range_end,
        anchor=anchor,
        window_duration=window_dur,
        step_duration=step_dur,
        warmup_duration=warmup_dur,
        timezone=tz,
        freeze_anchor=freeze_anchor,
    )

def load_time_config_yaml(filepath: str) -> TimeConfig:
    """
    [PURPOSE]: Load YAML configuration file and parse into TimeConfig object.
    [DEPENDENCIES]: yaml, parse_time_config.
    [ARGS]: filepath — Path to YAML file.
    [RETURNS]: TimeConfig instance.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return parse_time_config(data)
