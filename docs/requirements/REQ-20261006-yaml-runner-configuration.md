# Requirement Specification (REQ)

- **ID**: REQ-20261006-yaml-runner-configuration
- **Title**: Chuyển runner runtime options sang YAML thay vì CLI flags
- **Created Date**: 2026-10-06
- **Status**: Draft

---

## 1. Overview & Objective
Cho phép chạy các entrypoint bằng lệnh ngắn `python run_backtest.py` hoặc `python run_pipeline.py`. Toàn bộ runtime setting được chỉnh trong YAML: dataset descriptor, EMA periods, bar limit, risk-free rate, WFO window/trial count và report directory.

## 2. Scope & Target Architectural Layer
`run_backtest.py` đọc `config/backtest.yaml` cho strict production flow. `run_pipeline.py` đọc `config/pipeline.yaml` cho legacy research/WFO flow. Dataset physical range/hash vẫn thuộc Dataset YAML; `bar_limit` chỉ giới hạn số bar sau strict loading, không sửa file nguồn hoặc DataRange contract.

## 3. Detailed Approach & Steps
1. Tạo typed YAML parsing/validation helpers for runner config, with explicit errors for missing descriptor, non-positive bar limit, and invalid EMA/WFO values.
2. Tạo `config/backtest.yaml`: dataset definition path, EMA fast/slow periods, optional bar limit, and risk-free rate.
3. Đổi `run_backtest.py` đọc config mặc định, thêm EMA features, optionally take first configured bars only after strict DatasetLoader success, then run/evaluate.
4. Tạo `config/pipeline.yaml`: dataset definition path, benchmark/WFO options, n_windows, n_trials, and reports directory.
5. Đổi `run_pipeline.py` đọc YAML mặc định thay cho runtime CLI options while retaining strict DatasetLoader.
6. Thêm config parsing tests and runner E2E; README ghi command ngắn và vị trí config.

## 4. Files TO Modify
- [ ] `config/backtest.yaml` (new)
- [ ] `config/pipeline.yaml` (new)
- [ ] `src/config/runner.py` (new)
- [ ] `run_backtest.py`
- [ ] `run_pipeline.py`
- [ ] `tests/config/test_runner_config.py` (new)
- [ ] `tests/e2e/test_run_backtest_cli.py`
- [ ] `README.md`
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261006-yaml-runner-configuration.md`

## 5. Acceptance Criteria
- [ ] `python run_backtest.py` takes no strategy/dataset/timing CLI flags.
- [ ] `python run_pipeline.py` takes no WFO/benchmark/report CLI flags.
- [ ] Invalid YAML settings fail clearly before a backtest starts.
- [ ] `bar_limit` never bypasses DatasetLoader validation and never modifies the source dataset.
- [ ] WFO windows/trials and report path are editable only in YAML.
- [ ] Existing strict runner E2E stays green.

## 6. Verification Plan
- [ ] `python -m unittest tests.config.test_runner_config tests.e2e.test_run_backtest_cli`
- [ ] `python run_backtest.py` using the configured test/real descriptor.

## 7. Data and Config Access Confirmation Required
- `D:\reverse_indi\data\valm15-indivip_signal.csv`: read-only E2E fixture verification.
- Existing YAML under `D:\reverse_indi\config\`: inspect only to reuse the repository's descriptor/config conventions; no source dataset data is changed.

## 8. Result
- Status: Pending approval and YAML-read confirmation
- Date: 2026-10-06
