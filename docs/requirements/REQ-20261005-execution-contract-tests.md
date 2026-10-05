# Requirement Specification (REQ)

- **ID**: REQ-20261005-execution-contract-tests
- **Title**: Khóa Execution Contracts và kiểm thử đường khớp lệnh T+1
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Khóa 7 execution contracts hiện được hỗ trợ: không fill cùng nến tạo signal, pending từ nến kế tiếp, market fill theo Open(T+1), adverse slippage, fee theo giá fill, limit chỉ fill khi chạm, và một order chỉ complete fill tối đa một lần. Limit order luôn fill đúng `limit_price` khi nến chạm; không áp dụng price improvement theo giá open.

## 2. Scope & Target Architectural Layer
Tác động `src/trading/execution/` và đường tích hợp `BacktestEngine`. Không triển khai partial fill, intrabar replay thực, stop/TP/SL, hoặc funding integration. Volatility slippage và funding chỉ được unit test theo khả năng component hiện hữu; wiring production được ghi nhận là future work.

## 3. Detailed Approach & Steps
1. Tách rõ eligibility và reference-price của `OHLCFillModel`: market dùng open (fallback close); limit chỉ eligible khi high/low chạm và reference price luôn là `limit_price`.
2. Để `ExecutionEngine` áp dụng adverse slippage và tính fee trên giá thực thi sau slippage; giới hạn giá limit để giá fill luôn đúng `limit_price`.
3. Reject cấu hình slippage âm thay vì âm thầm clamp về 0.
4. Viết critical contract tests cho EX-01 đến EX-07: T→T+1, chống look-ahead, market lifecycle/double-fill, slippage, fee, và ranh giới limit BUY/SELL.
5. Viết unit tests cho `PerpetualFundingModel` và `VolatilitySlippageModel`; đánh dấu rõ wiring production của funding/ATR slippage chưa thuộc scope.
6. Chạy targeted tests và cập nhật status/REQ kết quả.

## 4. Files TO Modify
- [ ] `src/trading/execution/fill_model.py`
- [ ] `src/trading/execution/broker.py`
- [ ] `src/trading/execution/slippage.py`
- [ ] `tests/execution/test_execution_contracts.py` (new)
- [ ] `tests/execution/test_execution_models.py` (new)
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261005-execution-contract-tests.md`

## 5. Acceptance Criteria
- [ ] EX-01 đến EX-07 đều có critical automated coverage.
- [ ] Lệnh từ candle T chỉ fill từ candle T+1; market fill theo Open(T+1), fallback Close khi thiếu Open.
- [ ] BUY slippage bất lợi tăng giá, SELL giảm giá; fee dựa trên giá fill thực tế.
- [ ] BUY và SELL limit, khi đã đủ điều kiện chạm giá, luôn fill đúng `limit_price`, kể cả khi open gap qua giá đó.
- [ ] Filled order bị loại khỏi pending và không double fill.
- [ ] Không thay đổi phạm vi EX-08 đến EX-12 ngoài unit test component đã tồn tại.

## 6. Verification Plan
- [x] `python -m unittest discover -s tests/execution -p "test_*.py"` — 9 tests passed.
- [ ] `python -m unittest tests.audit.test_timing_fix tests.temporal.test_lookahead_adversarial` — attempted after YAML-read permission; blocked before backtest because legacy dataset config supplies a storage format rejected by the strict `StorageReference` contract.

## 7. Result
- Status: Targeted execution contracts passed (9 tests); self-contained T+1 backtest passed. Legacy regression suite is blocked by incompatible legacy dataset configuration before execution begins.
- Date: 2026-10-05
