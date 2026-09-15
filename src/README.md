# Source Code Engine Modules (`src/`)

Thư mục chứa toàn bộ logic xử lý định lượng cho Pipeline Quant Lab (Fibo Zone-Registry + Projection + ATR Ratchet).

## Danh sách Modules & Chức năng

### 1. [data_feed.py](file:///d:/reverse_indi/src/data_feed.py)
- **Mục đích**: Tải dữ liệu nến M15 OHLCV, tính ATR Wilder RMA (period=14), và xác định các điểm xoay Swing High/Low chuẩn causal.
- **Hàm chính**: `load_m15_ohlcv()`, `calculate_causal_atr()`, `calculate_causal_swings()`.
- **Phụ thuộc**: `numpy`, `pandas`.

### 2. [zone_engine.py](file:///d:/reverse_indi/src/zone_engine.py)
- **Mục đích**: Đọc danh sách Zone từ `config/zones.yaml`, lọc theo preset (`tier1_only`, `tier1_plus_extension`, `full_with_harmonic`), và tính biên độ buffer động `± (zone_buffer_k * ATR)`.
- **Hàm chính**: `load_active_zones()`, `filter_zones_by_preset()`, `compute_dynamic_zone_bounds()`.
- **Phụ thuộc**: `pyyaml`, `numpy`.

### 3. [projection_engine.py](file:///d:/reverse_indi/src/projection_engine.py)
- **Mục đích**: Dự phóng hình học Target Zone tiếp theo trước khi giá tới dựa trên swing range đã xác nhận.
- **Hàm chính**: `project_target_zone()`.
- **Phụ thuộc**: Direct swing validation (`confirmed_at_bar <= current_bar`).

### 4. [state_machine.py](file:///d:/reverse_indi/src/state_machine.py)
- **Mục đích**: Quản lý chuỗi 5 trạng thái (Stage 0 -> Stage 4 Entry), lọc hướng theo Equilibrium Premium/Discount, lọc nến trigger (Rejection Wick / Engulfing), invalidation timeout, và force-reset trạng thái tại ranh giới WFO.
- **Hàm chính**: `SetupStateMachine`, `check_trigger_candle()`.
- **Phụ thuộc**: Called by `execution_simulator.py`.

### 5. [atr_ratchet.py](file:///d:/reverse_indi/src/atr_ratchet.py)
- **Mục đích**: Trailing stop Ratchet ATR 14/3.0 khóa cứng (khớp số học Pine Script `indicator_vip.pine`) với ngưỡng kích hoạt linh hoạt.
- **Hàm chính**: `ATRRatchetExit.initialize_stop()`, `ATRRatchetExit.update_ratchet()`.
- **Phụ thuộc**: Called by `execution_simulator.py`.

### 6. [execution_simulator.py](file:///d:/reverse_indi/src/execution_simulator.py)
- **Mục đích**: Mô phỏng khớp lệnh kép (**Wick Touch** optimistic vs **Bar Close** pessimistic), quản trị vốn tính lot theo risk %, trừ phí commission (4bps), ATR slippage và 8h Perp Funding Rate.
- **Hàm chính**: `run_trade_simulation()`.
- **Phụ thuộc**: `state_machine.py`, `atr_ratchet.py`.

### 7. [wfo_splitter.py](file:///d:/reverse_indi/src/wfo_splitter.py)
- **Mục đích**: Chia dữ liệu thành các cửa sổ Purged & Embargoed Walk-Forward (guardrail min 300 lệnh), cắt lệnh còn mở tại ranh giới, và reset state machine sang Stage 0.
- **Hàm chính**: `PurgedWFOSplitter.generate_splits()`, `PurgedWFOSplitter.enforce_boundary_reset()`.
- **Phụ thuộc**: Called by `run_pipeline.py`.

### 8. [optimizer.py](file:///d:/reverse_indi/src/optimizer.py)
- **Mục đích**: Chạy Optuna Bayesian optimization cho từng cửa sổ IS, kiểm tra vùng Plateau quanh trial top để loại bỏ nhiễu tham số nhọn.
- **Hàm chính**: `run_optuna_study()`, `evaluate_plateau_champion()`, `objective_function()`.
- **Phụ thuộc**: `optuna`, `execution_simulator.py`.

### 9. [alpha_decay.py](file:///d:/reverse_indi/src/alpha_decay.py)
- **Mục đích**: Phân tích suy giảm Alpha 2 trục (Thời gian: 3M/6M/1Y; Số lệnh: 50/100/250 trades).
- **Hàm chính**: `evaluate_time_horizons()`, `evaluate_trade_count_horizons()`, `compute_alpha_decay_summary()`.
- **Phụ thuộc**: Called by `run_pipeline.py`.

### 10. [reporting.py](file:///d:/reverse_indi/src/reporting.py)
- **Mục đích**: Đánh giá hiệu năng OOS, log độ ổn định tham số, so sánh fill lệnh, tính Drag ratio và kết luận **PASS / WARN / FAIL**.
- **Hàm chính**: `generate_pipeline_report()`.
- **Phụ thuộc**: Output generator for CLI.
