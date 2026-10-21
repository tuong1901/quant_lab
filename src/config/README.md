# Configuration layer — maintained strict runner

Production flow: `config/backtest.yaml` -> `load_backtest_runner_config()` ->
`BacktestRunnerConfig` -> `run_strict_backtest()`. Dataset descriptors are loaded
separately by `Dataset.from_yaml()` in the runner.

## Validation and runtime wiring

`runner.py` resolves the dataset path relative to the configuration YAML and
validates positive integer EMA/ATR periods, fast < slow, optional positive bar
limit, finite positive capital/leverage/sizing/exit settings, finite non-negative
fees/slippage in bps, boolean short permission, and finite risk-free rate > -1.
It requires ATR stops and `stop_first` intrabar priority.
`BacktestRunnerConfig.__post_init__` also validates direct Python construction.

The configured ATR period is forwarded to feature calculation. The runner starts
the clock at the first selected candle and records dataset identity including
version in ExecutionContext. BacktestEngine receives an explicit market symbol
separate from run ID; old callers retain the run-ID symbol fallback. Empty
selected data is rejected before engine creation.

## Function logs

```powershell
.\venv\Scripts\python.exe run_backtest.py
.\venv\Scripts\python.exe run_backtest.py --log-level DEBUG
```

Only the CLI configures handlers. INFO logs resolved settings, dataset descriptor
and identity, row counts/time range, feature periods, constructor settings and
completion counts. DEBUG adds configuration helper and engine sizing/exit/bar
traces. Records contain time, level, module and function name. Full DataFrames
and raw YAML are not logged. Diagnostics go to stderr and append UTF-8 records
to `logs/backtest.log` relative to the working directory; reports stay on stdout.
Failures include traceback/context. CLI exit codes: 0 success, 2 existing
account-depletion path, 1 other handled runtime failures.

## Focused verification

```powershell
.\venv\Scripts\python.exe -B -m unittest discover -s tests/config -p test_runner_config.py -v
.\venv\Scripts\python.exe -B -m unittest discover -s tests/engine -p test_strict_runner_wiring.py -v
```

These 11 tests use synthetic in-memory inputs and mocked disk boundaries:
numerical validation, ATR propagation, non-BTC/pre-2020 integration, constructor
compatibility, parameter forwarding, function logs and CLI behavior. They do not
certify the ATR algorithm or all trading-engine behavior. Real-data execution
requires separate file-access permission.

## Historical legacy design (not the production path)

The material below describes `loader.py`, `models.py`, `validation.py` and old
exports. Their environment/experiment/pipeline YAML files were retired.
Legacy boolean/timezone/snapshot issues remain outside the strict-runner repair.
`exceptions.py` is shared by the maintained runner and legacy API.

Centralized configuration layer for Quant Lab responsible for parsing YAML declarations into typed configuration objects, resolving inter-config references, performing validation, resolving deterministic anchors (`now`), and generating reproducible config snapshots.

---

## Architecture Principles & Boundaries

1. **Ranh Giới Rõ Ràng giữa Config và Domain**:
   - YAML chỉ là cú pháp khai báo bên ngoài.
   - Các domain module (`execution`, `portfolio`, `market_data`, `backtest`, `strategies`) **tuyệt đối không tự đọc file YAML hoặc parse YAML**.
   - `ConfigLoader` chịu trách nhiệm đọc YAML và parse thành các Dataclass typed bất biến (`ExperimentConfig`, `ExecutionConfig`, `PortfolioConfig`, `DatasetRefConfig`, `DefaultEnvConfig`).

2. **Giải Quyết Neo `now` Deterministic**:
   - Khi cấu hình khai báo `range.end: now`, `ConfigLoader` sẽ tự động quy đổi `now` thành mốc Datetime UTC duy nhất (`resolved_anchor`) tại thời điểm load.
   - Giúp đảm bảo 100% tính tái tạo (Reproducibility): cùng config + cùng dataset + cùng resolved_anchor = kết quả backtest 100% trùng khớp.

3. **Tự Động Resolve Liên Kết (Reference Resolution)**:
   - `experiments.yaml` tham chiếu đến các cấu hình con bằng tên:
     - `environment.config: default` -> `config/default.yaml`
     - `datasets: {strategy: btcusdt_15m, execution: btcusdt_1m}` -> `config/datasets.yaml`
     - `execution.config: default` -> `config/execution.yaml`
     - `portfolio.config: default` -> `config/portfolio.yaml`
   - Nếu reference không tồn tại, hệ thống ném ngoại lệ `ConfigReferenceError` lập tức.

4. **Khai Báo Cấu Hình Tập Trung (`config/*.yaml`)**:
   - **[`config/default.yaml`](file:///d:/reverse_indi/config/default.yaml)**: System & Environment settings.
   - **[`config/datasets.yaml`](file:///d:/reverse_indi/config/datasets.yaml)**: Named dataset definitions.
   - **[`config/execution.yaml`](file:///d:/reverse_indi/config/execution.yaml)**: Execution subsystem presets.
   - **[`config/portfolio.yaml`](file:///d:/reverse_indi/config/portfolio.yaml)**: Portfolio & Risk presets.
   - **[`config/experiments.yaml`](file:///d:/reverse_indi/config/experiments.yaml)**: Experiment compositions.
   - **[`config/search.yaml`](file:///d:/reverse_indi/config/search.yaml)**: Search space definitions for optimization.

---

## Components (`src/config/`)

- **[exceptions.py](file:///d:/reverse_indi/src/config/exceptions.py)**: Custom exceptions (`ConfigError`, `ConfigFileNotFoundError`, `ConfigParseError`, `ConfigValidationError`, `ConfigReferenceError`, `ConfigCompatibilityError`).
- **[models.py](file:///d:/reverse_indi/src/config/models.py)**: Immutable dataclasses (`DefaultEnvConfig`, `DatasetRefConfig`, `ExecutionConfig`, `PortfolioConfig`, `ExperimentTimeConfig`, `ExperimentConfig`).
- **[validation.py](file:///d:/reverse_indi/src/config/validation.py)**: Engine `validate_experiment_config(exp_config)` (kiem tra mâu thuẫn symbol/venue, leverage risk limit).
- **[loader.py](file:///d:/reverse_indi/src/config/loader.py)**: Class `ConfigLoader` (`load_default_env`, `load_dataset`, `load_execution`, `load_portfolio`, `load_experiment`, `snapshot_experiment`).
- **[__init__.py](file:///d:/reverse_indi/src/config/__init__.py)**: Export Public API.

---

## Strict backtest YAML

`python run_backtest.py` uses `config/backtest.yaml` as its production configuration. Its `account`, `risk`, `exit`, and `execution` sections control capital/leverage, fixed or percent-risk sizing, ATR stop, fixed-R target, fees, and slippage. If one candle touches both exits, the strict contract applies `stop_first`.

The legacy YAML research path has been retired. The maintained configuration contract is `config/backtest.yaml` plus a descriptor in `config/datasets/`.

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/config/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/config -v
```
- Historical result only: 19 tests passed before retirement. Current legacy tests
  reference removed YAML and outdated domain constructors; this is not a current passing suite.
