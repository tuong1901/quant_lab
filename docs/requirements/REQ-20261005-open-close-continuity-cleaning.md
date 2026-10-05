# Requirement Specification (REQ)

- **ID**: REQ-20261005-open-close-continuity-cleaning
- **Title**: Làm đẹp tính liên tục Open-Close của OHLCV
- **Created Date**: 2026-10-05
- **Status**: Completed

---

## 1. Overview & Objective
Thêm bước data-cleaning có kiểm soát vào strict canonicalization: với mọi nến từ nến thứ hai, nếu `open[i] != close[i-1]`, thay `open[i]` bằng `close[i-1]`. Dữ liệu đã làm đẹp là dữ liệu canonical được hash, validate và chuyển xuống feature/backtest.

## 2. Scope & Target Architectural Layer
Chỉ thay đổi `src/data` canonicalization và contract tests. Không sửa CSV nguồn; không thay đổi `high`, `low`, `close` hoặc `volume` trừ khi yêu cầu được xác nhận rõ.

## 3. Detailed Approach & Steps
1. Thêm hàm pure `enforce_open_close_continuity()` sau parse timestamp/numeric và trước OHLCV validation/hash.
2. Chỉ thay `open` của nến thứ hai trở đi; nến đầu giữ nguyên.
3. Hash canonical sẽ phản ánh giá open đã được làm đẹp; loader trả DataFrame đã làm đẹp.
4. Thêm critical/mutation tests: mismatch được sửa, first candle giữ nguyên, hash ổn định sau cleaning, và xử lý trường hợp corrected open nằm ngoài high/low.

## 4. Files TO Modify
- [ ] `src/data/versioning.py`
- [ ] `src/data/README.md`
- [ ] `tests/data/test_critical_contracts.py`
- [ ] `tests/mutation/test_data_contract_mutations.py`
- [ ] `PROJECT_STATUS.md`

## 5. Acceptance Criteria
- [ ] Nến thứ hai trở đi có `open == close` của nến ngay trước trong canonical output.
- [ ] CSV/Parquet nguồn không bị sửa.
- [ ] Hash và loader dùng dữ liệu sau cleaning.
- [ ] Tests chứng minh đúng behavior và không che giấu OHLC violation.

## 6. Verification Plan
- [ ] Chạy targeted critical + mutation data tests.

## 7. Result
- Status: Passed
- Date: 2026-10-05
- Decision: Nếu `close[i-1]` nằm ngoài `[low[i], high[i]]`, giữ strict rejection; không tự sửa high/low.
- Verification: `python -m unittest tests.data.test_critical_contracts tests.mutation.test_data_contract_mutations` passed (15 tests).
