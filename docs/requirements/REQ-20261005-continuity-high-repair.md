# Requirement Specification (REQ)

- **ID**: REQ-20261005-continuity-high-repair
- **Title**: Sửa High sau khi continuity-clean Open
- **Created Date**: 2026-10-05
- **Status**: Draft

---

## 1. Overview & Objective
Khi canonicalization thay `open[i]` bằng `close[i-1]`, nếu `high[i] < open[i]` thì nâng `high[i]` lên đúng `open[i]`. Mục tiêu là duy trì bất đẳng thức OHLC sau data cleaning để strict pipeline có thể tiếp tục, mà không sửa CSV nguồn.

## 2. Scope & Target Architectural Layer
Chỉ đổi data canonicalization và các contract tests liên quan. Không thay `low`, `close`, `volume`, timestamp hay file CSV/Parquet nguồn. Trường hợp corrected open vẫn thấp hơn low sẽ tiếp tục bị strict loader từ chối.

## 3. Detailed Approach & Steps
1. Mở rộng `enforce_open_close_continuity()` để sau khi ép open, nâng high bằng open tại các row có `high < open`.
2. Giữ nguyên candle đầu tiên và mọi high đã lớn hơn hoặc bằng open.
3. Bổ sung critical test chứng minh high được sửa chính xác, hash/loader dùng candle canonical mới.
4. Đổi mutation test: một low-bound violation còn phải bị reject, không bị high repair che mất.
5. Chạy data contract tests, rồi chạy E2E data-to-evaluation trên 64 nến thật đã được cấp quyền đọc.

## 4. Files TO Modify
- [ ] `src/data/versioning.py`
- [ ] `src/data/README.md`
- [ ] `tests/data/test_critical_contracts.py`
- [ ] `tests/mutation/test_data_contract_mutations.py`
- [ ] `tests/e2e/test_strict_data_pipeline.py`
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261005-continuity-high-repair.md`

## 5. Acceptance Criteria
- [ ] Với `high[i] < close[i-1]`, canonical output có `open[i] == high[i] == close[i-1]`.
- [ ] Source CSV/Parquet không bị sửa.
- [ ] Low-bound và mọi OHLC violation khác không liên quan vẫn bị loader reject.
- [ ] Data contract suite và E2E Dataset → Evaluation pass.

## 6. Verification Plan
- [ ] `python -m unittest tests.data.test_critical_contracts tests.mutation.test_data_contract_mutations`
- [ ] `python -m unittest tests.e2e.test_strict_data_pipeline`

## 7. Data Access Confirmation
- `D:\reverse_indi\data\valm15-indivip_signal.csv` was approved by the user in this task for read-only 64-candle E2E execution.

## 8. Result
- Status: Pending approval
- Date: 2026-10-05
