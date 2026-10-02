"""
[PURPOSE]: Public API exports for src.experiments package.
[DEPENDENCIES]: config, window, run, planner.
"""

from src.experiments.config import (
    TimeConfig,
    Duration,
    DurationUnit,
    ConfigError,
    parse_duration,
    parse_time_config,
    load_time_config_yaml,
)
from src.experiments.window import TimeWindow
from src.experiments.run import ExperimentRun
from src.experiments.planner import (
    TimePlanner,
    DatasetRange,
    PlanningError,
)
from src.experiments.optimizer import (
    run_optuna_study,
    evaluate_plateau_champion,
    objective_function,
)

__all__ = [
    "TimeConfig",
    "Duration",
    "DurationUnit",
    "ConfigError",
    "parse_duration",
    "parse_time_config",
    "load_time_config_yaml",
    "TimeWindow",
    "ExperimentRun",
    "TimePlanner",
    "DatasetRange",
    "PlanningError",
    "run_optuna_study",
    "evaluate_plateau_champion",
    "objective_function",
]
