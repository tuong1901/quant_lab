# Requirement Specification (REQ)

- **ID**: REQ-20261005-e2e-data-to-evaluation
- **Title**: Chứng minh E2E từ strict market data đến evaluation metrics
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Mở rộng E2E production-path proof để kiểm chứng đầy đủ `Dataset → DatasetLoader → feature → strategy → BacktestEngine → BasicMetrics`. Báo cáo kết quả từ một slice giới hạn 64 nến M15 thật, không sửa dữ liệu nguồn.

## 2. Scope & Target Architectural Layer
Chỉ sửa test E2E và documentation trạng thái. Production data, strategy, loader, backtest và evaluation code không bị thay đổi. Test đọc duy nhất CSV được liệt kê ở mục 7.

## 3. Detailed Approach & Steps
1. Mở rộng E2E test hiện hữu để gọi `calculate_basic_metrics(result)` sau BacktestEngine.
2. Assert các invariant evaluation: equity curve cùng độ dài portfolio history, `net_pnl = final_equity - initial_capital`, và `return_pct` nhất quán.
3. Chạy E2E bằng 64 candle thực, báo bars, signals, orders, fills, final equity, net PnL, return, trade count và win rate.
4. Cập nhật REQ/status với kết quả; không xuất report artifact và không ghi đè dữ liệu nguồn.

## 4. Files TO Modify
- [ ] `tests/e2e/test_strict_data_pipeline.py`
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261005-e2e-data-to-evaluation.md`

## 5. Acceptance Criteria
- [ ] E2E chứng minh DatasetLoader, feature, strategy, backtest và evaluation chạy liên thông.
- [ ] 64 nến thật được đọc nhưng không bị sửa.
- [ ] BasicMetrics khớp BacktestResult về final equity, net PnL và return percentage.
- [ ] Test pass mà không cần output report file.

## 6. Verification Plan
- [ ] `python -m unittest tests.e2e.test_strict_data_pipeline`

## 7. Data Access Confirmation Required
- File: `D:\reverse_indi\data\valm15-indivip_signal.csv`
- Purpose: Read first 64 candles into a temporary test fixture, then execute the strict E2E path through evaluation.
- Operation: Read only; source file is never modified or executed.

## 8. Result
- Status: In progress; data access approved by user for this E2E run.
- Date: 2026-10-05
