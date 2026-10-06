# Requirement Specification (REQ)

- **ID**: REQ-20261005-continuity-high-repair
- **Title**: Clamp Open sau khi continuity-clean để giữ nguyên High
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Chỉ khi `open[i] != close[i-1]`, canonicalization mới thử thay `open[i]` bằng `close[i-1]`. Nếu giá open thử thay đó lớn hơn `high[i]`, đặt lại `open[i] = high[i]`; không bao giờ sửa `high`. Mục tiêu là làm liên tục open-close khi có thể mà vẫn giữ nguyên range giá của candle nguồn.

## 2. Scope & Target Architectural Layer
Chỉ đổi data canonicalization và các contract tests liên quan. Không thay `high`, `low`, `close`, `volume`, timestamp hay file CSV/Parquet nguồn. Trường hợp open thử thay thấp hơn low sẽ tiếp tục bị strict loader từ chối.

## 3. Detailed Approach & Steps
1. Mở rộng `enforce_open_close_continuity()` để chỉ xử lý row có open khác close nến trước; thử continuity open, rồi clamp open về high nếu continuity value vượt high.
2. Giữ nguyên candle đầu tiên, mọi candle đã continuous, và toàn bộ high gốc.
3. Bổ sung critical test chứng minh open được clamp chính xác, hash/loader dùng candle canonical mới.
4. Đổi mutation test: một low-bound violation còn phải bị reject, không bị open clamp che mất.
5. Chạy data contract tests, rồi chạy E2E data-to-evaluation trên đoạn 34 nến hợp lệ nằm trong 64 nến thật đã được cấp quyền đọc.

## 4. Files TO Modify
- [x] `src/data/versioning.py`
- [x] `src/data/README.md`
- [x] `tests/data/test_critical_contracts.py`
- [x] `tests/mutation/test_data_contract_mutations.py`
- [x] `tests/e2e/test_strict_data_pipeline.py`
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261005-continuity-high-repair.md`

## 5. Acceptance Criteria
- [x] Với `high[i] < close[i-1]`, canonical output có `open[i] == high[i]` và high nguồn không bị thay đổi.
- [x] Candle có `open[i] == close[i-1]` giữ nguyên open/high.
- [x] Source CSV/Parquet không bị sửa.
- [x] Low-bound và mọi OHLC violation khác không liên quan vẫn bị loader reject.
- [x] Data contract suite và E2E Dataset → Evaluation pass.

## 6. Verification Plan
- [x] `python -m unittest tests.data.test_critical_contracts tests.mutation.test_data_contract_mutations` — 16 tests passed.
- [x] `python -m unittest tests.e2e.test_strict_data_pipeline` — 1 E2E test passed using a valid 34-candle real-data run.

## 7. Data Access Confirmation
- `D:\reverse_indi\data\valm15-indivip_signal.csv` was approved by the user in this task for read-only 64-candle E2E execution.

## 8. Result
- Status: Passed
- Date: 2026-10-06
- Decision: only discontinuous opens are considered for continuity cleaning; a candidate open above high is clamped to high, while high itself remains unchanged.
- Date: 2026-10-05
