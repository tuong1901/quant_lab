# Requirement Specification (REQ)

- **ID**: REQ-20261005-portfolio-contract-tests
- **Title**: Khóa P0 Portfolio Contracts bằng lifecycle và accounting tests
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Thiết lập bộ P0 test cho chuỗi invariant `Fill → Position → realized PnL → unrealized PnL → fees → equity`. Xác minh vòng đời position và accounting hiện có, không thay đổi mô hình giao dịch khi test chưa chỉ ra defect.

## 2. Scope & Target Architectural Layer
Chỉ tác động `src/trading/portfolio/` qua automated tests. P0 gồm open/add/reduce/close/reversal, duplicate fill, fee, mark-to-market, equity reconciliation và golden lifecycle. Margin, RiskManager, funding integration và multi-symbol isolation là P1/future scope, không triển khai trong REQ này.

## 3. Detailed Approach & Steps
1. Viết test công thức LONG/SHORT realized và unrealized PnL, gồm lời/lỗ/hòa vốn.
2. Viết 18 P0 contract tests cho open, weighted average với quantity không bằng nhau, partial/full close, reversal hai chiều, fee accounting, duplicate fill, MTM và equity reconciliation.
3. Thêm Golden Portfolio lifecycle: open → mark → partial close → mark → reversal → final mark; kiểm tra toàn bộ state cuối.
4. Nếu một P0 test phát hiện defect, sửa tối thiểu ở portfolio source và thêm regression assertion; nếu tất cả pass, chỉ thay đổi test/documentation.
5. Chạy targeted suite và cập nhật REQ/status với kết quả.

## 4. Files TO Modify
- [x] `tests/portfolio/test_portfolio_contracts.py` (new)
- [x] `tests/portfolio/README.md` (new)
- [x] `src/trading/portfolio/portfolio.py` (no P0 defect demonstrated; unchanged)
- [x] `src/trading/portfolio/account.py` (no P0 defect demonstrated; unchanged)
- [x] `src/trading/portfolio/pnl.py` (no P0 defect demonstrated; unchanged)
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261005-portfolio-contract-tests.md`

## 5. Acceptance Criteria
- [x] PF-01 to PF-10 invariants have automated P0 coverage.
- [x] Open, add, reduce, close, and reversal preserve correct side, quantity, average entry, and realized PnL.
- [x] Fees reduce account equity while remaining distinct from realized trading PnL.
- [x] MTM changes only unrealized PnL/equity/margin snapshot; closing transfers unrealized PnL to realized PnL without creating value.
- [x] Duplicate FillId cannot affect the ledger twice.
- [x] Golden sequence ends LONG/SHORT state, PnL, fees, and equity exactly as specified.

## 6. Verification Plan
- [x] `python -m unittest discover -s tests/portfolio -p "test_*.py"` — 14 test methods passed; parameterized cases cover all 18 P0 contract IDs.

## 7. Result
- Status: Passed — no P0 portfolio defect demonstrated.
- Date: 2026-10-05
