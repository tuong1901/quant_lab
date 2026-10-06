# Requirement Specification (REQ)

- **ID**: REQ-20261005-e2e-data-to-evaluation
- **Title**: Chứng minh E2E từ strict market data đến evaluation metrics
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Mở rộng E2E production-path proof để kiểm chứng đầy đủ `Dataset → DatasetLoader → feature → strategy → BacktestEngine → BasicMetrics`. Báo cáo kết quả từ 34 nến M15 thật hợp lệ trong slice 64 nến được phép đọc, không sửa dữ liệu nguồn.

## 2. Scope & Target Architectural Layer
Chỉ sửa test E2E và documentation trạng thái. Production data, strategy, loader, backtest và evaluation code không bị thay đổi. Test đọc duy nhất CSV được liệt kê ở mục 7.

## 3. Detailed Approach & Steps
1. Mở rộng E2E test hiện hữu để gọi `calculate_basic_metrics(result)` sau BacktestEngine.
2. Assert các invariant evaluation: equity curve cùng độ dài portfolio history, `net_pnl = final_equity - initial_capital`, và `return_pct` nhất quán.
3. Chạy E2E bằng 34 candle thực hợp lệ, báo bars, signals, orders, fills, final equity, net PnL, return, trade count và win rate.
4. Cập nhật REQ/status với kết quả; không xuất report artifact và không ghi đè dữ liệu nguồn.

## 4. Files TO Modify
- [x] `tests/e2e/test_strict_data_pipeline.py`
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261005-e2e-data-to-evaluation.md`

## 5. Acceptance Criteria
- [x] E2E chứng minh DatasetLoader, feature, strategy, backtest và evaluation chạy liên thông.
- [x] 34 nến thật hợp lệ được đọc nhưng không bị sửa.
- [x] BasicMetrics khớp BacktestResult về final equity, net PnL và return percentage.
- [x] Test pass mà không cần output report file.

## 6. Verification Plan
- [x] `python -m unittest tests.e2e.test_strict_data_pipeline` — 1 test passed.

## 7. Data Access Confirmation Required
- File: `D:\reverse_indi\data\valm15-indivip_signal.csv`
- Purpose: Read the first 64 candles, use the known-valid row 30–63 run (34 candles) in a temporary fixture, then execute the strict E2E path through evaluation.
- Operation: Read only; source file is never modified or executed.

## 8. Result
- Status: Passed — Dataset → Evaluation ran on 34 valid real M15 candles within the approved 64-candle source slice.
- Date: 2026-10-06
- Date: 2026-10-05
