# Requirement Specification (REQ)

- **ID**: REQ-20261005-split-feature-indicators
- **Title**: Tách Feature Indicator Engine thành các chỉ báo độc lập
- **Created Date**: 2026-10-05
- **Status**: In Progress

---

## 1. Overview & Objective
Chuyển file gộp `src/features/indicators.py` thành package `src/features/indicators/` để mỗi **chỉ báo hoàn chỉnh** có đúng một module riêng, dễ đọc, test và mở rộng mà không thay đổi thuật toán hiện tại.

## 2. Scope & Target Architectural Layer
Chỉ tác động feature engineering. Giữ nguyên API công khai `from src.features import ...` và cập nhật internal imports/callers cần thiết. Không thay đổi công thức ATR, swing, Trend Chính, Trend Phụ hay signal.

## 3. Detailed Approach & Steps
1. Tạo package `src/features/indicators/`.
2. Di chuyển `calculate_causal_atr` vào `atr.py`; `calculate_causal_swings` vào `swings.py`.
3. Gom toàn bộ chỉ báo VIP Trend vào `vip_trend.py`: Trend Chính, Trend Phụ, logic signal và hàm tính end-to-end.
4. `__init__.py` re-export API công khai.
5. Cập nhật import callers, thêm/điều chỉnh test import và cập nhật README/status.

## 4. Files TO Modify
- [ ] `src/features/indicators.py` (remove after migration)
- [ ] `src/features/indicators/__init__.py` (new)
- [ ] `src/features/indicators/atr.py` (new)
- [ ] `src/features/indicators/swings.py` (new)
- [ ] `src/features/indicators/vip_trend.py` (new)
- [ ] `src/features/__init__.py`
- [ ] `run_backtest.py`
- [ ] `run_pipeline.py`
- [ ] `tests/e2e/test_strict_data_pipeline.py`
- [ ] `src/features/README.md` (new)
- [ ] `PROJECT_STATUS.md`

## 5. Acceptance Criteria
- [ ] Mỗi indicator nêu trong scope nằm trong module riêng.
- [ ] Công thức/behavior giữ nguyên.
- [ ] Public imports từ `src.features` hoạt động.
- [ ] Pipeline, backtest và targeted E2E vẫn chạy.

## 6. Verification Plan
- [ ] Compile feature package.
- [ ] Chạy targeted E2E strict data pipeline và tests feature liên quan.

## 7. Result
- Status: Pending approval
- Date: 2026-10-05
