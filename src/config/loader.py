"""
Config Loader Engine (`src/config/loader.py`).

Parses YAML declarations into typed configuration objects, resolves references, and creates reproducible snapshots.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import yaml

from src.market_data.market import Market
from src.market_data.timeframe import Timeframe
from src.market_data.dataset import StorageReference
from src.config.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigValidationError,
    ConfigReferenceError,
)
from src.config.models import (
    SystemConfig,
    ClockConfig,
    ReproducibilityConfig,
    BoundaryConfig,
    DefaultEnvConfig,
    DatasetRefConfig,
    FillConfig,
    SlippageConfig,
    FeeConfig,
    FundingConfig,
    ExecutionConfig,
    AccountConfig,
    LeverageConfig,
    PositionConfig,
    RiskConfig,
    PortfolioConfig,
    ExperimentTimeConfig,
    ExperimentConfig,
)
from src.config.validation import validate_experiment_config


class ConfigLoader:
    """
    [PURPOSE]: Loader service that reads YAML config files, resolves inter-config references, and instantiates typed models.
    [DEPENDENCIES]: Uses PyYAML, Config exceptions, typed models, and validate_experiment_config.
    [ARGS]: config_dir — Base directory containing configuration YAML files (default 'config').
    [RETURNS]: ConfigLoader instance.
    [SIDE EFFECTS]: Reads files from local storage.
    """

    def __init__(self, config_dir: str = "config") -> None:
        """
        [PURPOSE]: Initialize ConfigLoader with base config directory.
        """
        self.config_dir = config_dir

    def _read_yaml(self, filename: str) -> Dict[str, Any]:
        """
        [PURPOSE]: Helper method to read and parse a YAML file cleanly.
        """
        file_path = os.path.join(self.config_dir, filename)
        if not os.path.exists(file_path):
            raise ConfigFileNotFoundError(f"Configuration file not found: '{file_path}'")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except yaml.YAMLError as e:
            raise ConfigParseError(f"Failed to parse YAML file '{file_path}': {str(e)}")

    def load_default_env(self, name: str = "default") -> DefaultEnvConfig:
        """
        [PURPOSE]: Load environment and system configuration from default.yaml.
        """
        data = self._read_yaml("default.yaml")
        sys_data = data.get("system", {})
        clock_data = data.get("clock", {})
        repro_data = data.get("reproducibility", {})
        bound_data = data.get("boundary", {})

        sys_cfg = SystemConfig(
            name=str(sys_data.get("name", "quant_lab")),
            timezone=str(sys_data.get("timezone", "UTC")),
        )
        clock_cfg = ClockConfig(mode=str(clock_data.get("mode", "historical")))
        repro_cfg = ReproducibilityConfig(
            seed=int(repro_data.get("seed", 42)),
            freeze_anchor=bool(repro_data.get("freeze_anchor", True)),
        )
        bound_cfg = BoundaryConfig(policy=str(bound_data.get("policy", "strict")))

        return DefaultEnvConfig(
            name=name,
            system=sys_cfg,
            clock=clock_cfg,
            reproducibility=repro_cfg,
            boundary=bound_cfg,
        )

    def load_dataset(self, name: str) -> DatasetRefConfig:
        """
        [PURPOSE]: Load dataset configuration by name reference from datasets.yaml.
        """
        data = self._read_yaml("datasets.yaml")
        datasets_dict = data.get("datasets", {})

        if name not in datasets_dict:
            raise ConfigReferenceError(
                f"Dataset reference '{name}' not found in datasets.yaml. Available datasets: {list(datasets_dict.keys())}"
            )

        ds_data = datasets_dict[name]
        m_data = ds_data.get("market", {})
        storage_data = ds_data.get("storage_reference", {})

        market = Market(
            venue=str(m_data.get("venue", "")),
            symbol=str(m_data.get("symbol", "")),
            market_type=str(m_data.get("market_type", "")),
            quote_currency=str(m_data.get("quote_currency", "")),
        )

        tf = Timeframe.parse(ds_data.get("timeframe", "15m"))
        storage_ref = StorageReference(
            type=str(storage_data.get("type", "local")),
            path=str(storage_data.get("path", "")),
        )

        return DatasetRefConfig(
            name=name,
            dataset_id=str(ds_data.get("dataset_id", "")),
            version=int(ds_data.get("version", 1)),
            market=market,
            timeframe=tf,
            storage_reference=storage_ref,
        )

    def load_execution(self, name: str = "default") -> ExecutionConfig:
        """
        [PURPOSE]: Load execution configuration preset by name reference from execution.yaml.
        """
        data = self._read_yaml("execution.yaml")
        exec_dict = data.get("execution", {})

        if name not in exec_dict:
            raise ConfigReferenceError(
                f"Execution preset reference '{name}' not found in execution.yaml. Available presets: {list(exec_dict.keys())}"
            )

        e_data = exec_dict[name]
        f_data = e_data.get("fill", {})
        timing_data = f_data.get("timing", {})
        slip_data = e_data.get("slippage", {})
        fee_data = e_data.get("fee", {})
        fund_data = e_data.get("funding", {})

        fill_cfg = FillConfig(
            model=str(f_data.get("model", "ltf_replay")),
            timing_market_order=str(timing_data.get("market_order", "next_bar")),
        )
        slip_cfg = SlippageConfig(
            model=str(slip_data.get("model", "percentage")),
            value=float(slip_data.get("value", 0.0002)),
        )
        fee_cfg = FeeConfig(
            maker=float(fee_data.get("maker", 0.0001)),
            taker=float(fee_data.get("taker", 0.0002)),
        )
        fund_cfg = FundingConfig(enabled=bool(fund_data.get("enabled", False)))

        return ExecutionConfig(
            name=name,
            fill=fill_cfg,
            slippage=slip_cfg,
            fee=fee_cfg,
            funding=fund_cfg,
        )

    def load_portfolio(self, name: str = "default") -> PortfolioConfig:
        """
        [PURPOSE]: Load portfolio and risk configuration preset by name reference from portfolio.yaml.
        """
        data = self._read_yaml("portfolio.yaml")
        port_dict = data.get("portfolio", {})

        if name not in port_dict:
            raise ConfigReferenceError(
                f"Portfolio preset reference '{name}' not found in portfolio.yaml. Available presets: {list(port_dict.keys())}"
            )

        p_data = port_dict[name]
        acc_data = p_data.get("account", {})
        lev_data = p_data.get("leverage", {})
        pos_data = p_data.get("position", {})
        risk_data = p_data.get("risk", {})

        acc_cfg = AccountConfig(
            initial_capital=float(acc_data.get("initial_capital", 10000.0)),
            currency=str(acc_data.get("currency", "USDT")),
        )
        lev_cfg = LeverageConfig(
            mode=str(lev_data.get("mode", "fixed")),
            value=float(lev_data.get("value", 1.0)),
        )
        pos_cfg = PositionConfig(
            allow_short=bool(pos_data.get("allow_short", True)),
            max_position_size=float(pos_data.get("max_position_size", 1.0)),
            max_notional=float(pos_data.get("max_notional", 50000.0)),
        )
        risk_cfg = RiskConfig(
            max_leverage=float(risk_data.get("max_leverage", 5.0)),
            max_exposure=float(risk_data.get("max_exposure", 50000.0)),
        )

        return PortfolioConfig(
            name=name,
            account=acc_cfg,
            leverage=lev_cfg,
            position=pos_cfg,
            risk=risk_cfg,
        )

    def load_experiment(
        self, name: str, anchor_now: Optional[datetime] = None
    ) -> ExperimentConfig:
        """
        [PURPOSE]: Resolve references and build a complete ExperimentConfig from experiments.yaml.
        [DEPENDENCIES]: Resolves env, dataset, execution, and portfolio references; calls validate_experiment_config.
        [ARGS]:
            name — Experiment string name.
            anchor_now — Optional datetime override for 'now' resolution to guarantee 100% reproducibility.
        [RETURNS]: Fully resolved ExperimentConfig.
        """
        data = self._read_yaml("experiments.yaml")
        exp_dict = data.get("experiments", {})

        if name not in exp_dict:
            raise ConfigReferenceError(
                f"Experiment '{name}' not found in experiments.yaml. Available experiments: {list(exp_dict.keys())}"
            )

        exp_data = exp_dict[name]

        # 1. Resolve sub-config references
        env_ref_name = exp_data.get("environment", {}).get("config", "default")
        env_cfg = self.load_default_env(env_ref_name)

        ds_refs = exp_data.get("datasets", {})
        strat_ds_ref_name = ds_refs.get("strategy")
        exec_ds_ref_name = ds_refs.get("execution")

        if not strat_ds_ref_name:
            raise ConfigValidationError(f"Experiment '{name}' missing 'datasets.strategy' reference.")
        if not exec_ds_ref_name:
            raise ConfigValidationError(f"Experiment '{name}' missing 'datasets.execution' reference.")

        strat_ds_cfg = self.load_dataset(strat_ds_ref_name)
        exec_ds_cfg = self.load_dataset(exec_ds_ref_name)

        exec_ref_name = exp_data.get("execution", {}).get("config", "default")
        exec_cfg = self.load_execution(exec_ref_name)

        port_ref_name = exp_data.get("portfolio", {}).get("config", "default")
        port_cfg = self.load_portfolio(port_ref_name)

        # 2. Resolve time configuration & deterministic 'now' anchor
        time_data = exp_data.get("time", {})
        mode = str(time_data.get("mode", "fixed"))
        range_data = time_data.get("range", {})

        start_raw = range_data.get("start")
        end_raw = range_data.get("end")

        if not start_raw:
            raise ConfigValidationError(f"Experiment '{name}' missing 'time.range.start'")
        if not end_raw:
            raise ConfigValidationError(f"Experiment '{name}' missing 'time.range.end'")

        start_dt = self._parse_iso_utc(start_raw)

        # Deterministic 'now' resolution
        resolved_anchor = anchor_now if anchor_now is not None else datetime.now(timezone.utc)
        if isinstance(end_raw, str) and end_raw.lower().strip() == "now":
            end_dt = resolved_anchor
        else:
            end_dt = self._parse_iso_utc(end_raw)

        win_data = time_data.get("window", {})
        step_data = time_data.get("step", {})
        warmup_data = time_data.get("warmup", {})

        time_cfg = ExperimentTimeConfig(
            mode=mode,
            start=start_dt,
            end=end_dt,
            resolved_anchor=resolved_anchor,
            window_duration=win_data.get("duration"),
            step_duration=step_data.get("duration"),
            warmup_bars=int(warmup_data.get("bars", 200)),
        )

        exp_config = ExperimentConfig(
            name=name,
            environment=env_cfg,
            strategy_dataset=strat_ds_cfg,
            execution_dataset=exec_ds_cfg,
            execution=exec_cfg,
            portfolio=port_cfg,
            time=time_cfg,
        )

        # 3. Perform cross-config validation
        validate_experiment_config(exp_config)

        return exp_config

    def _parse_iso_utc(self, val: Any) -> datetime:
        """
        [PURPOSE]: Helper to parse string or datetime to UTC-aware datetime.
        """
        if isinstance(val, datetime):
            dt = val
        elif isinstance(val, str):
            val_str = val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(val_str)
        else:
            raise ConfigValidationError(f"Cannot parse datetime from {val}")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def snapshot_experiment(self, exp_config: ExperimentConfig, output_dir: str) -> str:
        """
        [PURPOSE]: Save a 100% resolved snapshot YAML file of an ExperimentConfig into output_dir.
        [DEPENDENCIES]: Writes snapshot.yaml file for reproducibility.
        [ARGS]:
            exp_config — Resolved ExperimentConfig object.
            output_dir — Destination directory path.
        [RETURNS]: str Path of saved snapshot file.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        snapshot_dict = {
            "experiment_name": exp_config.name,
            "resolved_anchor": exp_config.time.resolved_anchor.isoformat(),
            "time": {
                "mode": exp_config.time.mode,
                "start": exp_config.time.start.isoformat(),
                "end": exp_config.time.end.isoformat(),
                "window_duration": exp_config.time.window_duration,
                "step_duration": exp_config.time.step_duration,
                "warmup_bars": exp_config.time.warmup_bars,
            },
            "strategy_dataset": {
                "name": exp_config.strategy_dataset.name,
                "dataset_id": exp_config.strategy_dataset.dataset_id,
                "version": exp_config.strategy_dataset.version,
                "identity": f"{exp_config.strategy_dataset.dataset_id}:v{exp_config.strategy_dataset.version}",
                "market": exp_config.strategy_dataset.market.to_dict(),
                "timeframe": str(exp_config.strategy_dataset.timeframe),
            },
            "execution_dataset": {
                "name": exp_config.execution_dataset.name,
                "dataset_id": exp_config.execution_dataset.dataset_id,
                "version": exp_config.execution_dataset.version,
                "identity": f"{exp_config.execution_dataset.dataset_id}:v{exp_config.execution_dataset.version}",
                "market": exp_config.execution_dataset.market.to_dict(),
                "timeframe": str(exp_config.execution_dataset.timeframe),
            },
            "execution_preset": exp_config.execution.name,
            "portfolio_preset": exp_config.portfolio.name,
        }

        file_path = os.path.join(output_dir, "config_snapshot.yaml")
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(snapshot_dict, f, sort_keys=False, allow_unicode=True)

        return file_path
