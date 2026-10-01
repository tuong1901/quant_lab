# Requirement Specification (REQ)

- **ID**: REQ-20261001-architecture-reorganization
- **Title**: Hợp nhất Kiến trúc, Khóa Biên Core & Chuẩn hóa Single Source of Truth (SSOT)
- **Created Date**: 2026-10-01
- **Status**: Draft (Updated with Strict Architectural Safeguards)

---

## 1. Overview & Objective

Hiện tại hệ thống tồn tại **5 vấn đề kiến trúc nghiêm trọng**:
1. **2 Lớp source cùng tồn tại**: Flat files (`src/*.py`) và subpackages (`src/<subpackage>/`) gây mất nhận diện *Single Source of Truth (SSOT)*.
2. **Nợ kiến trúc & Phá vỡ ranh giới (DAG Leak)**: Enum `PositionSide` bị import ngược từ `portfolio` vào `strategies/context.py` (`VIOLATION-01`).
3. **Nguy cơ trùng lặp trách nhiệm (Duplicate Implementations)**: Các module legacy (`wfo_splitter`, `zone_engine`, `projection_engine`, `execution_simulator`, `reporting`) nếu move ngây thơ sẽ tạo ra 2 nơi xử lý cùng 1 nghiệp vụ.
4. **Core chưa được khóa bằng Rule & Test Guardrail**: Agent AI có thể tự ý làm lệch `execution timing`, `fee drag`, `portfolio accounting`, `clock determinism`.
5. **Acceptance criteria trước đây quá đơn giản**: Chỉ dựa vào `156/156 PASS` (Green test không đồng nghĩa với Architecture đúng).

**MỤC TIÊU BÀI TASKS NÀY**:
Giải quyết dứt điểm 5 vấn đề trên, hợp nhất hoàn toàn về **Single Source of Truth (`src/<subpackage>/`)**, khóa biên Core tuyệt đối, và chứng nhận tính nhất quán hành vi (Golden Behavioral Baseline).

---

## 2. Scope & Architectural Boundaries

### 🔒 Core Layer (Khóa cứng - Frozen Boundaries)
Cấm mọi sự thay đổi về contract, timing, accounting hoặc determinism tại:
- `src/core/`: Types, Clock, IDs, Events, Exceptions
- `src/config/`: Models, Validation, Loader
- `src/environment/`: Registry, Factory, Context
- `src/market_data/`: Dataset, Hasher SHA-256, Loader validation
- `src/execution/`: ExecutionEngine, FillModel, Slippage, Fees, Funding 8h
- `src/portfolio/`: Account, Portfolio, Margin, RiskManager
- `src/backtest/`: BacktestEngine Causal T+1 Loop

### ⚡ Customization Layer (Nơi cho phép Refactor & Migration)
- `src/features/` & `src/indicators/`: Nhận mảng tính toán Fibo Zone Registry & Causal Projections.
- `src/strategies/`: Nhận mảng State Machine 5 giai đoạn & Trailing ATR Ratchet.
- `src/experiments/`: Nhận mảng Purged & Embargoed WFO Splitter & Optuna Optimizer.
- `src/evaluation/`: Nhận mảng Dual-axis Alpha Decay Tracker & Reporting Engine.
- Entrypoint `run_backtest.py`: CLI duy nhất thay thế `run_pipeline.py`.

---

## 3. Detailed Technical Approach & Mapping Matrix

### Step 1: Fix Architectural Violations & Strict DAG Boundary
1. **Khắc phục `VIOLATION-01`**: Di chuyển Enum `PositionSide` từ `src/portfolio/position.py` về `src/core/types.py`. Cập nhật tất cả import sites.
2. **Bổ sung DAG Architecture Guard Test**: Viết unit test tự động quét toàn bộ cây AST trong `src/strategies/` đảm bảo KHÔNG import bất kỳ module nào từ `src/portfolio/` hay `src/execution/`.

### Step 2: Mapping & Merging Legacy Flat Modules (No Duplicate Rule)
Mỗi trách nhiệm legacy CHỈ ĐƯỢC PHÉP có đúng 1 nơi thực thi duy nhất trong subpackage mới:

| Module Legacy | Vị trí SSOT Mới trong Subpackage | Trách nhiệm được hợp nhất (Single Responsibility) | Action đối với file flat cũ |
| :--- | :--- | :--- | :--- |
| `src/trend_engine.py` | `src/features/trend_ribbon.py` | Thuật toán 3 đường nấc thang VIP Trend Indicator | Hợp nhất & Xóa file cũ |
| `src/zone_engine.py` | `src/features/zones.py` | Dynamic ATR Zone Buffer expansion & Fibo preset | Hợp nhất & Xóa file cũ |
| `src/projection_engine.py` | `src/features/projections.py` | Dự phóng Target Zone hình học Causal Swing | Hợp nhất & Xóa file cũ |
| `src/state_machine.py` | `src/strategies/vip_strategy.py` | Strategy logic State Machine 5 giai đoạn | Hợp nhất & Xóa file cũ |
| `src/atr_ratchet.py` | `src/strategies/exits/atr_ratchet.py` | Exit rule Trailing ATR Ratchet 14/3.0 | Hợp nhất & Xóa file cũ |
| `src/execution_simulator.py` | `src/execution/fill_model.py` | Tích hợp Dual Fill (`Wick Touch` vs `Bar Close`) & Risk Sizing vào `FillModel` | Hợp nhất & Xóa file cũ |
| `src/wfo_splitter.py` | `src/experiments/splitter.py` | Purged & Embargoed Walk-Forward Splitter | Hợp nhất & Xóa file cũ |
| `src/optimizer.py` | `src/experiments/optimizer.py` | Optuna Plateau Champion Optimizer | Hợp nhất & Xóa file cũ |
| `src/alpha_decay.py` | `src/evaluation/alpha_decay.py` | Tracker suy giảm Alpha 2 trục | Hợp nhất & Xóa file cũ |
| `src/reporting.py` | `src/evaluation/reporting.py` | Reporting OOS verdict PASS/WARN/FAIL | Hợp nhất & Xóa file cũ |
| `src/data_feed.py` | `src/market_data/loader.py` | Tải dữ liệu M15 & Causal Swing Wilder RMA ATR | Hợp nhất & Xóa file cũ |

### Step 3: Golden Behavioral Baseline Setup
1. Trước khi xóa bất kỳ file flat nào, chạy 20 trials WFO của `run_pipeline.py` và lưu snapshot kết quả (Golden Baseline Equity Curve, Net PnL, Win Rate, Sharpe) ra `tests/fixtures/golden_baseline_v1.json`.
2. Sau khi migrate xong, runner mới `run_backtest.py` bắt buộc phải ra kết quả **khớp số học 100%** với file golden snapshot này (`same config + same dataset + same seed = exact same result`).

### Step 4: Lock Boundaries with Automated Integrity Rules
1. Tạo test case `tests/architecture/test_dag_guard.py` kiểm tra tĩnh (Static AST Check) việc tuân thủ ma trận phụ thuộc DAG.
2. Tạo test case `tests/architecture/test_core_immutability.py` khóa cứng các invariants của `HistoricalClock`, `Order`, `Fill`, `Account`, `Portfolio`.

---

## 4. Files TO Modify / Create

- [x] `docs/requirements/REQ-20261001-architecture-reorganization.md`
- [ ] `ARCHITECTURE.md` (Tài liệu hóa quy tắc khóa cứng Core & SSOT)
- [ ] `src/core/types.py` (Bổ sung `PositionSide` để fix `VIOLATION-01`)
- [ ] `src/strategies/context.py` (Cập nhật import `PositionSide` từ `src.core.types`)
- [ ] `src/features/zones.py` & `src/features/projections.py` & `src/features/trend_ribbon.py`
- [ ] `src/strategies/vip_strategy.py` & `src/strategies/exits/atr_ratchet.py`
- [ ] `src/execution/fill_model.py` (Tích hợp Dual Fill Simulator)
- [ ] `src/experiments/splitter.py` & `src/experiments/optimizer.py`
- [ ] `src/evaluation/alpha_decay.py` & `src/evaluation/reporting.py`
- [ ] `run_backtest.py` (Runner chuẩn duy nhất)
- [ ] `tests/architecture/test_dag_guard.py` (Architecture Guard Test)
- [ ] `tests/fixtures/golden_baseline_v1.json` (Golden Master Snapshot)
- [ ] Direct deletion of 10 legacy flat files in `src/` (`data_feed.py`, `zone_engine.py`, `projection_engine.py`, `state_machine.py`, `atr_ratchet.py`, `execution_simulator.py`, `wfo_splitter.py`, `optimizer.py`, `alpha_decay.py`, `reporting.py`, `trend_engine.py`).

---

## 5. Strict Acceptance Criteria (5 Tiêu Chí Cứng)

1. **Single Source of Truth (SSOT)**:
   - Xóa bỏ 100% 10 file flat legacy trong `src/`. Dưới `src/` CHỈ TỒN TẠI các subpackages kiến trúc (`core`, `config`, `environment`, `market_data`, `features`, `strategies`, `execution`, `portfolio`, `backtest`, `evaluation`, `experiments`, `batch`, `generator`, `evolution`, `paper`).
2. **Architecture DAG Guard (Khắc phục VIOLATION-01)**:
   - `tests/architecture/test_dag_guard.py` CHẠY PASS 100%. Không có bất kỳ câu lệnh import trái phép nào từ `strategies -> portfolio/execution`.
3. **Golden Behavioral Baseline Verification**:
   - `run_backtest.py` cho ra kết quả khớp số học **100.0000%** so với `tests/fixtures/golden_baseline_v1.json` trên cùng dataset và seed.
4. **No Duplicate Implementation**:
   - Mọi trách nhiệm (Zone engine, Projection, State machine, Dual fill, WFO split) đều có đúng 1 nơi thực thi duy nhất trong subpackage.
5. **Architectural Certification Report**:
   - Xuất báo cáo chứng nhận kiến trúc tại `docs/architecture_certification_report.md` xác nhận Core đã được khóa và hệ thống đạt chuẩn SSOT.

---

## 6. Verification & Certification Commands

```bash
# 1. Chạy Architecture DAG Guard Test (Kiểm tra không vi phạm ranh giới)
.\venv\Scripts\python.exe -m unittest tests/architecture/test_dag_guard.py

# 2. Chạy toàn bộ 156+ Unit Tests
.\venv\Scripts\python.exe -m unittest discover -s tests

# 3. Chạy Golden Behavioral Baseline Verification (Khớp số học 100%)
.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json
```

---

## 7. Result
- Status: Approved (User Approved Migration Plan)
- Date: 2026-10-01
