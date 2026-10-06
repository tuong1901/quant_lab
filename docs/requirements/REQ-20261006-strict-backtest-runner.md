# Requirement Specification (REQ)

- **ID**: REQ-20261006-strict-backtest-runner
- **Title**: Chuyển run_backtest.py sang strict production backtest flow
- **Created Date**: 2026-10-06
- **Status**: Completed

---

## 1. Overview & Objective
Thay CLI `run_backtest.py` legacy/WFO simulator bằng entrypoint strict duy nhất: Dataset YAML → DatasetLoader → feature → strategy → BacktestEngine → BasicMetrics + EquityRiskMetrics + accounting reconciliation. Output phải cho người dùng thấy đầy đủ dòng tiền trước khi đưa ra kết quả cuối.

## 2. Scope & Target Architectural Layer
`run_backtest.py` chạy `EMAStrategy`, vì đây là strategy concrete duy nhất hiện có theo Strategy contract. VIP Trend hiện là indicator feature, chưa có strategy adapter nên không bị giả định là strategy runnable. `run_pipeline.py` legacy/WFO không bị sửa trong REQ này.

## 3. Detailed Approach & Steps
1. Xóa đường gọi `run_trade_simulation`, WFO, alpha-decay và legacy `reporting.py` khỏi `run_backtest.py`.
2. Thêm CLI strict yêu cầu `--dataset-definition`, cùng `--fast-period`, `--slow-period`, và optional `--risk-free-rate`.
3. Load dataset descriptor qua `Dataset.from_yaml` và `DatasetLoader`; tính EMA features theo strategy parameters.
4. Chạy `BacktestEngine(EMAStrategy(...))`, rồi `BasicMetrics` và `EquityRiskMetrics`.
5. In accounting reconciliation: initial, realized, fees, funding, account equity, unrealized, final equity, residual; sau đó in performance/risk metrics.
6. Thêm test CLI/integration dùng strict real-data fixture được cấp quyền đọc và cập nhật README/status.

## 4. Files TO Modify
- [x] `run_backtest.py`
- [x] `src/evaluation/metrics.py`
- [x] `src/evaluation/__init__.py`
- [x] `tests/e2e/test_run_backtest_cli.py` (new)
- [x] `README.md`
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261006-strict-backtest-runner.md`

## 5. Acceptance Criteria
- [x] `run_backtest.py` never imports or calls `run_trade_simulation`, WFO optimizer, alpha decay, or legacy reporting.
- [x] Runner only accepts a strict Dataset YAML descriptor and uses DatasetLoader.
- [x] Runner uses BacktestEngine and displays complete accounting reconciliation with zero residual within tolerance.
- [x] Runner prints performance/risk metrics from EquityRiskMetrics.
- [x] E2E CLI test proves the strict path using a bounded approved real-data fixture.

## 6. Verification Plan
- [x] `python -m unittest tests.e2e.test_run_backtest_cli tests.e2e.test_strict_data_pipeline` — 3 tests passed.
- [x] `python run_backtest.py --help` — passed.

## 7. Data Access Confirmation Required
- File: `D:\reverse_indi\data\valm15-indivip_signal.csv`
- Purpose: Read-only bounded fixture for the strict runner E2E test and sample CLI execution.

## 8. Result
- Status: Completed
- Date: 2026-10-06
- Result: `run_backtest.py` is now the strict production runner. The legacy WFO simulator remains isolated in `run_pipeline.py`.
- Date: 2026-10-06
