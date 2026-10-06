"""Typed configuration loaders for command-free project runners."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.config.exceptions import ConfigFileNotFoundError, ConfigParseError, ConfigValidationError


@dataclass(frozen=True)
class BacktestRunnerConfig:
    """Configuration consumed by the strict production backtest runner."""

    dataset_definition: str
    fast_period: int
    slow_period: int
    bar_limit: int | None
    risk_free_rate: float


@dataclass(frozen=True)
class PipelineRunnerConfig:
    """Configuration consumed by the legacy research pipeline runner."""

    dataset_definition: str
    benchmark_trials: int | None
    n_trials: int
    n_windows: int
    reports_dir: str


def _read_yaml_mapping(path: str | Path) -> tuple[dict[str, Any], Path]:
    """
    [PURPOSE]: Read one runner YAML file and require a mapping at its root.
    [DEPENDENCIES]: PyYAML and config exceptions.
    [ARGS]: path — YAML file path.
    [RETURNS]: Parsed mapping and resolved file path.
    [SIDE EFFECTS]: Reads a file and raises a clear config error for missing or malformed YAML.
    """
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise ConfigFileNotFoundError(f"Runner configuration not found: {resolved}")
    try:
        payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ConfigParseError(f"Malformed runner YAML {resolved}: {error}") from error
    if not isinstance(payload, dict):
        raise ConfigValidationError(f"Runner configuration {resolved} must be a YAML mapping.")
    return payload, resolved


def _mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ConfigValidationError(f"Runner configuration requires mapping '{key}'.")
    return value


def _positive_int(value: Any, name: str, allow_none: bool = False) -> int | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigValidationError(f"'{name}' must be a positive integer.")
    return value


def _relative_path(value: Any, config_path: Path, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"'{name}' must be a non-empty path string.")
    candidate = Path(value)
    return str((config_path.parent / candidate).resolve()) if not candidate.is_absolute() else str(candidate)


def load_backtest_runner_config(path: str | Path = "config/backtest.yaml") -> BacktestRunnerConfig:
    """
    [PURPOSE]: Parse and validate strict backtest runtime settings from YAML.
    [DEPENDENCIES]: _read_yaml_mapping and validation helpers.
    [ARGS]: path — Backtest YAML path.
    [RETURNS]: Immutable typed backtest configuration.
    [SIDE EFFECTS]: Reads YAML and raises config errors before data loading starts.
    """
    payload, config_path = _read_yaml_mapping(path)
    strategy = _mapping(payload, "strategy")
    data = _mapping(payload, "data")
    evaluation = _mapping(payload, "evaluation")
    fast_period = _positive_int(strategy.get("fast_period"), "strategy.fast_period")
    slow_period = _positive_int(strategy.get("slow_period"), "strategy.slow_period")
    if fast_period >= slow_period:
        raise ConfigValidationError("'strategy.fast_period' must be smaller than 'strategy.slow_period'.")
    bar_limit = _positive_int(data.get("bar_limit"), "data.bar_limit", allow_none=True)
    risk_free_rate = evaluation.get("risk_free_rate")
    if isinstance(risk_free_rate, bool) or not isinstance(risk_free_rate, (int, float)):
        raise ConfigValidationError("'evaluation.risk_free_rate' must be numeric.")
    return BacktestRunnerConfig(
        dataset_definition=_relative_path(payload.get("dataset_definition"), config_path, "dataset_definition"),
        fast_period=fast_period,
        slow_period=slow_period,
        bar_limit=bar_limit,
        risk_free_rate=float(risk_free_rate),
    )


def load_pipeline_runner_config(path: str | Path = "config/pipeline.yaml") -> PipelineRunnerConfig:
    """
    [PURPOSE]: Parse and validate research-pipeline runtime settings from YAML.
    [DEPENDENCIES]: _read_yaml_mapping and validation helpers.
    [ARGS]: path — Pipeline YAML path.
    [RETURNS]: Immutable typed pipeline configuration.
    [SIDE EFFECTS]: Reads YAML and raises config errors before data loading starts.
    """
    payload, config_path = _read_yaml_mapping(path)
    walk_forward = _mapping(payload, "walk_forward")
    benchmark_trials = _positive_int(payload.get("benchmark_trials"), "benchmark_trials", allow_none=True)
    return PipelineRunnerConfig(
        dataset_definition=_relative_path(payload.get("dataset_definition"), config_path, "dataset_definition"),
        benchmark_trials=benchmark_trials,
        n_trials=_positive_int(walk_forward.get("n_trials"), "walk_forward.n_trials"),
        n_windows=_positive_int(walk_forward.get("n_windows"), "walk_forward.n_windows"),
        reports_dir=_relative_path(payload.get("reports_dir"), config_path, "reports_dir"),
    )
