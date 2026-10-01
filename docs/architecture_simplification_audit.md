# Architecture Simplification & Consolidation Audit (Bản Gộp Thư Mục Vật Lý)

- **Date**: 2026-10-01
- **Target Repository**: `d:\reverse_indi`
- **Goal**: Gộp 11 subpackages rải rác hiện tại thành **6 Thư Mục Miền Vật Lý (6 Physical Domain Folders)** đúng theo mô hình tư duy khối của người dùng.

---

## 🏛️ ĐỀ XUẤT GỘP FOLDER THÀNH 6 KHỐI VẬT LÝ CHI TIẾT (PHYSICAL DOMAIN MERGE)

Thay vì để 11-14 subpackages nằm rải rác dưới `src/`, hệ thống sẽ được **gộp vật lý thành 6 thư mục khối chính**:

```text
src/
├── 1. data/           # [XỬ LÝ DỮ LIỆU]: Loader (load_m15_ohlcv), Dataset Catalog, Schema & UTC Validation, SHA-256 Hasher
├── 2. environment/    # [MÔI TRƯỜNG & TÀI KHOẢN]: EnvironmentFactory, Account Balance, Position, Portfolio Accounting, Margin, RiskManager (Risk-Sizing)
├── 3. features/       # [CHỈ BÁO & FEATURES]: Wilder RMA ATR, Swing Engine, VIP Trend Ribbon 3-line stepper, Dynamic Fibo Zones & Projections
├── 4. strategies/     # [CHIẾN LƯỢC & QUY TẮC]: Strategy Contract (on_bar), SetupStateMachine 5 giai đoạn, ATRRatchetExit, Signal & Context
├── 5. engine/         # [ĐỘNG CƠ KHỚP LỆNH & BACKTEST]: BacktestEngine (Causal T+1), ExecutionEngine, FillModel (OHLC & M1 intrabar), Slippage, Fee, Funding 8h, Trade Simulator, WFO Optuna Optimizer
└── 6. evaluation/     # [ĐÁNH GIÁ & BÁO CÁO]: BasicMetrics, Dual-Axis Alpha Decay Tracker, Pipeline Report Exporter (Markdown/JSON/CSV)
```

---

## 📋 MA TRẬN GỘP SUBPACKAGES (PACKAGE MERGE MAPPING)

| Folder Cũ (14 Subpackages) | Folder Vật Lý Mới (6 Core Domain Folders) | Nội dung & Trách nhiệm sau khi Gộp |
| :--- | :--- | :--- |
| `src/market_data/` | **`src/data/`** | Đổi tên gọn thành `data/`. Chứa loader, catalog, versioning SHA-256, UTC validator. |
| `src/environment/` <br>+ `src/portfolio/` | **`src/environment/`** | Gộp Portfolio accounting, Account, Position, Margin & RiskManager vào trong `environment/`. |
| `src/features/` | **`src/features/`** | Giữ nguyên `features/`. Chứa toàn bộ toán chỉ báo (`indicators.py`) và mảng Fibo zones (`zones.py`). |
| `src/strategies/` | **`src/strategies/`** | Giữ nguyên `strategies/`. Chứa Hợp đồng Strategy, SetupStateMachine 5 giai đoạn & Trailing ATR Ratchet. |
| `src/execution/` <br>+ `src/backtest/` | **`src/engine/`** | Gộp Execution Engine (Order, Fill, FillModel, Slippage, Fee, Funding) & Backtest Loop (BacktestEngine, Simulator, WFO Optimizer) vào duy nhất **`src/engine/`**. |
| `src/evaluation/` | **`src/evaluation/`** | Giữ nguyên `evaluation/`. Chứa metrics, Alpha Decay tracker & Reporting exporter. |
| `src/batch/`, `src/generator/`, `src/evolution/`, `src/paper/` | ❌ **REMOVED** | Xóa bỏ 4 folder rác scaffold rỗng không sử dụng. |

---

## 🛡️ BẢO ĐẢM TÍNH ĐÚNG ĐẮN VÀ BEHAVIOR (BEHAVIORAL INVARIANTS)

1. **Trading Semantics 100% Không Đổi**:
   - `T+1 Causal Execution Timing` giữ nguyên.
   - `Slippage, Commission 4bps, Funding 8h` giữ nguyên.
   - `Portfolio Accounting & PnL` giữ nguyên.
   - `HistoricalClock` tiến thời gian 1 chiều giữ nguyên.
2. **Kiểm tra Test Suite**:
   - Cập nhật import paths trong `tests/` để tương thích với 6 folder vật lý mới.
   - Tất cả 115 unit tests phải **PASS 100%**.
3. **Kiểm tra Golden Baseline**:
   - Running `run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` bắt buộc đạt **PASSED 100.0000% NUMERICAL MATCH**.

---

## 🗓️ TRÌNH TỰ THỰC HIỆN GỘP FOLDER (MIGRATION SEQUENCE)

1. **Bước 1**: Di chuyển các file từ `src/market_data/` sang `src/data/`, từ `src/portfolio/` sang `src/environment/`, và từ `src/execution/` & `src/backtest/` sang `src/engine/`.
2. **Bước 2**: Xóa các thư mục cũ đã dọn sạch (`market_data`, `portfolio`, `execution`, `backtest`, `batch`, `generator`, `evolution`, `paper`).
3. **Bước 3**: Cập nhật import paths trong `src/`, `run_backtest.py`, `scripts/` và `tests/`.
4. **Bước 4**: Chạy `python -m unittest discover -s tests` (Đảm bảo PASS 100%).
5. **Bước 5**: Chạy `python run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` (Đảm bảo PASSED 100.0000% MATCH).
6. **Bước 6**: Cập nhật tài liệu `ARCHITECTURE.md` và xuất Báo cáo Chứng nhận Tinh gọn thành công.

---

**Vui lòng xác nhận phê duyệt Kế hoạch Gộp 6 Thư Mục Vật Lý này để tôi tiến hành thực hiện ngay!**
