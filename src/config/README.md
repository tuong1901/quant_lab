# Config Layer Subsystem (`src/config/` & `config/*.yaml`)

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

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/config/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/config -v
```
- **19/19 Unit tests PASS 100%** (Thời gian chạy ~0.09s).
