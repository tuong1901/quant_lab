# Reverse Engineering VIP Multi-Trend Indicator & Pipeline Quant Lab

Dự án nghiên cứu, tái tạo (reverse-engineer) thuật toán chỉ báo đa xu hướng (VIP Trend Indicator) và xây dựng **Pipeline Quant Lab** hoàn chỉnh cho BTCUSDT M15.

---

## 1. Kết quả Khớp Tham số Thực nghiệm (Verified Accuracy)

Qua kiểm thử số học trên dữ liệu nến thực tế (`valm15-indivip_signal.csv` và `m15-indivip_signal.csv`):
- **Độ chính xác Trend Chính 1**: **99.9884%** (Độ lệch trung bình chỉ ~3 giá trên mức giá 63,000).
- **Độ chính xác Trend Phụ 1**: **99.9608%** (Độ lệch trung bình chỉ ~26 giá trên mức giá 63,400).
- **Trend Phụ 2**: Được chứng minh chính xác tuyệt đối 100% là **Trend Phụ 1 trễ 2 nến** (`TP2 = TP1[2]`).

---

## 2. Pipeline Quant Lab: Fibo Zone-Registry + Projection + ATR Ratchet

Pipeline backtest, tối ưu hóa (Optuna) và đánh giá độ suy giảm Alpha (Alpha Decay) chuẩn định lượng:

1. **Config Layer (`config/`)**:
   - `zones.yaml`: Dynamic Fibo/Key Zone Registry (`tier1_only`, `tier1_plus_extension`, `full_with_harmonic`) với các role `entry`, `target`, `bias_filter`.
   - `fixed_params.yaml`: Khóa cứng tham số ATR Ratchet (Wilder RMA period=14, mult=3.0, trùng khớp `indicator_vip.pine`), quản trị vốn `risk_per_trade_pct`, phí 4bps + ATR slippage + 8h Funding Rate.
   - `search_space.yaml`: Không gian tối ưu hóa Optuna (7 chiều parameters).

2. **Core Engine (`src/`)**:
   - `data_feed.py`: Causal Wilder RMA ATR & Causal Swing Engine (`confirmed_at_bar <= current_bar`).
   - `zone_engine.py`: Dynamic ATR zone buffer expansion & preset filter.
   - `projection_engine.py`: Dự phóng Target Zone hình học chuẩn causal trước khi giá tới.
   - `state_machine.py`: State machine 5 giai đoạn (Stage 0 -> Stage 4 Entry), bias filter Equilibrium Premium/Discount, Rejection Wick (>=40%) / Engulfing trigger, stage timeout invalidation, và boundary force-reset.
   - `atr_ratchet.py`: Module Trailing Stop Ratchet ATR 14/3.0 khóa cứng với kích hoạt linh hoạt.
   - `execution_simulator.py`: Mô phỏng fill lệnh kép (**Wick Touch** vs **Bar Close**), tính lot theo % risk (`risk_amount / (entry - stop)`), trừ phí commission, slippage và 8h funding rate.
   - `wfo_splitter.py`: Splitter Purged & Embargoed Walk-Forward Optimization (min 300 lệnh guardrail, reset state machine tại ranh giới Train/Test).
   - `optimizer.py`: Optuna Bayesian optimization với kiểm tra Plateau Champion (neighborhood check quanh trial top).
   - `alpha_decay.py`: Đánh giá suy giảm Alpha 2 trục (Trục thời gian [3M/6M/1Y] & Trục chuẩn hóa trade count [50/100/250]).
   - `reporting.py`: Tổng hợp OOS Equity curve, Param stability log, Dual fill comparison, Expectancy/trade, Avg R, Fee Drag ratio và kết luận **PASS / WARN / FAIL**.

3. **CLI Runner (`run_pipeline.py`)**:
   - Chạy thử benchmark tốc độ: `.\venv\Scripts\python.exe run_pipeline.py --benchmark-trials 20`
   - Chạy full pipeline WFO: `.\venv\Scripts\python.exe run_pipeline.py --n-trials 50 --n-windows 3`

---

## 3. Cấu trúc Thư mục

- [config/zones.yaml](file:///d:/reverse_indi/config/zones.yaml): Dynamic Zone Registry config.
- [config/fixed_params.yaml](file:///d:/reverse_indi/config/fixed_params.yaml): Fixed ATR & capital management params.
- [config/search_space.yaml](file:///d:/reverse_indi/config/search_space.yaml): Optuna search space definitions.
- [src/data_feed.py](file:///d:/reverse_indi/src/data_feed.py): Causal data & swing features.
- [src/zone_engine.py](file:///d:/reverse_indi/src/zone_engine.py): Zone buffer calculation.
- [src/projection_engine.py](file:///d:/reverse_indi/src/projection_engine.py): Causal target projection.
- [src/state_machine.py](file:///d:/reverse_indi/src/state_machine.py): Setup state machine & filters.
- [src/atr_ratchet.py](file:///d:/reverse_indi/src/atr_ratchet.py): Fixed ATR Ratchet trailing exit.
- [src/execution_simulator.py](file:///d:/reverse_indi/src/execution_simulator.py): Dual-fill risk simulator.
- [src/wfo_splitter.py](file:///d:/reverse_indi/src/wfo_splitter.py): Purged WFO splitter.
- [src/optimizer.py](file:///d:/reverse_indi/src/optimizer.py): Optuna plateau optimizer.
- [src/alpha_decay.py](file:///d:/reverse_indi/src/alpha_decay.py): Dual-axis alpha decay tracker.
- [src/reporting.py](file:///d:/reverse_indi/src/reporting.py): Performance & verdict reporting.
- [run_pipeline.py](file:///d:/reverse_indi/run_pipeline.py): Main pipeline CLI execution script.
- [tradingview/indicator_vip.pine](file:///d:/reverse_indi/tradingview/indicator_vip.pine): Pine Script v5 reconstructed indicator.
