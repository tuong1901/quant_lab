# Requirement Specification (REQ)

- **ID**: REQ-20261006-evaluation-accounting-reconciliation
- **Title**: Hiển thị đầy đủ accounting reconciliation trong evaluation
- **Created Date**: 2026-10-06
- **Status**: Completed

---

## 1. Overview & Objective
Bổ sung breakdown rõ ràng để người dùng đánh giá final equity: realized PnL, unrealized PnL, fees, funding, account equity trước MTM và final equity sau MTM. Chứng minh bằng invariant accounting thay vì chỉ hiển thị một số final equity.

## 2. Scope & Target Architectural Layer
Chỉ tác động evaluation output/value objects và strict E2E assertion. Không đổi Portfolio accounting, fill pricing, fee calculation, strategy, hay dữ liệu nguồn.

## 3. Detailed Approach & Steps
1. Mở rộng `BasicMetrics` với `unrealized_pnl`, `funding_paid`, `account_equity`, và reconciliation residual.
2. Tính invariant: `final_equity = initial + realized - fees - funding + unrealized`.
3. Thêm formatter read-only cho evaluation summary để CLI/test/report caller có thể in bảng đầy đủ.
4. Bổ sung unit/E2E tests cho fee deduction, open-position unrealized PnL, và reconciliation.
5. Chạy evaluation unit tests cùng strict E2E trên data fixture đã được cấp quyền.

## 4. Files TO Modify
- [x] `src/evaluation/metrics.py`
- [x] `src/evaluation/__init__.py`
- [x] `src/evaluation/README.md`
- [x] `tests/evaluation/test_metrics.py`
- [x] `tests/e2e/test_strict_data_pipeline.py`
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261006-evaluation-accounting-reconciliation.md`

## 5. Acceptance Criteria
- [x] Evaluation exposes realized, unrealized, fees, funding, account equity, and final equity distinctly.
- [x] Reconciliation residual is zero within numeric tolerance in test fixtures.
- [x] A compact human-readable summary shows the full breakdown through `run_backtest.py`.
- [x] Existing BasicMetrics consumers remain compatible.

## 6. Verification Plan
- [x] `python -m unittest tests.evaluation.test_metrics tests.evaluation.test_equity_risk_metrics` — 14 tests passed.
- [x] `python -m unittest tests.e2e.test_strict_data_pipeline` — passed with reconciliation assertions.

## 7. Data Access Confirmation Required
- File: `D:\reverse_indi\data\valm15-indivip_signal.csv`
- Purpose: Read-only strict E2E verification on the existing 34-candle valid test fixture.

## 8. Result
- Status: Passed; accounting breakdown is now part of the strict runner output.
- Date: 2026-10-06
- Date: 2026-10-06
