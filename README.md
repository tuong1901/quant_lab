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

## 2. Triết Lý Thiết Kế 4 Chiều (4-Dimension Engineering Framework)

Hệ thống được phát triển theo định hướng kiến trúc 4 chiều nghiêm ngặt:

1. **Dimension 1 — Correctness (Được xây dựng đầu tiên)**:
   - Tập trung xây dựng bộ khung MVP: `core`, `environment`, `market_data`, `experiments`, `backtest`.
   - **Mục tiêu tối thượng**: `same config + same dataset + same seed = same result` (100% Deterministic & Reproducible).
2. **Dimension 2 — Simplicity (Giữ sự đơn giản tối đa)**:
   - Chưa tích hợp mã phức tạp (Ray, GA, AI/LLM, WebSocket, Paper trading, 1000 strategies engine) khi chưa cần thiết.
   - Thư mục được chuẩn bị sẵn làm skeleton, mã nguồn ngắn gọn, dễ đọc, không over-engineering.
3. **Dimension 3 — Scalability (Mở rộng quy mô từng bước)**:
   - Chỉ nâng cấp quy mô sau khi kiểm chứng tính đúng đắn trên single experiment: `1 strategy` → `10 strategies` → `100 strategies` → `1000 strategies`.
   - Quyết định dùng Vectorization, Caching, Multiprocessing hay Ray dựa trên benchmark thực tế, không dùng mặc định từ đầu.
4. **Dimension 4 — Evolvability (Khả năng tiến hóa không phá vỡ Core)**:
   - Trừu tượng hóa hoàn hảo cho phép mở rộng luồng: `Indicator` → `Strategy` → `Generator` → `Evolution` → `Batch` → `Paper` mà **không cần chỉnh sửa hay làm vỡ `Core` và `Backtest`**.

---

## 3. Cấu trúc Thư mục & Hệ thống Module (10-Phase Architecture)


Dự án được tổ chức theo kiến trúc **10-Phase Enterprise Quant Engine** với phân tách trách nhiệm rõ ràng (SRP - Single Responsibility Principle):

```text
quant_lab/
├── config/             # [PHASE 0] File cấu hình hệ thống (Zones, Fixed parameters, Search spaces)
├── data/               # Dữ liệu nến & tick lịch sử (M15 CSV/Parquet)
├── experiments/        # [PHASE 0] Jupyter Notebooks & Scratch research scripts
├── logs/               # Log hệ thống khi chạy backtest, optimization và paper trading
├── reports/            # Output báo cáo định lượng (Walk-Forward OOS, Alpha Decay, HTML tearsheets)
├── scripts/            # Script chạy CLI entrypoints (Backtest, WFO, Batch, Evolution, Paper)
├── tests/              # Unit test và Integration test tự động
├── tradingview/        # Mã nguồn Pine Script v5 chỉ báo VIP
└── src/                # Mã nguồn Python chính (14 Packages tương ứng 10 Phase)
```

---

### 📂 Chi Tiết Thư Mục Mã Nguồn (`src/`)

#### 🔹 **[PHASE 0] Environment & Core System Primitives**
- [src/core/](file:///d:/reverse_indi/src/core/): Chứa các kiểu dữ liệu nền tảng không thay đổi (Immutable Primitives):
  - [types.py](file:///d:/reverse_indi/src/core/types.py): Định nghĩa Enum `Side` (BUY/SELL), `OrderType` (MARKET/LIMIT), `TimeFrame`.
  - [clock.py](file:///d:/reverse_indi/src/core/clock.py): Đồng hồ mô phỏng thời gian Causal (`SimulationClock`).
  - [events.py](file:///d:/reverse_indi/src/core/events.py): Các sự kiện `MarketDataEvent`, `SignalEvent`, `OrderEvent`, `FillEvent`.
  - [orders.py](file:///d:/reverse_indi/src/core/orders.py), [fills.py](file:///d:/reverse_indi/src/core/fills.py), [positions.py](file:///d:/reverse_indi/src/core/positions.py), [portfolio.py](file:///d:/reverse_indi/src/core/portfolio.py): Data models quản lý Lệnh, Khớp lệnh, Vị thế và Trạng thái Danh mục.
  - [exceptions.py](file:///d:/reverse_indi/src/core/exceptions.py): Các ngoại lệ tùy chỉnh (`LookaheadBiasError`, `InsufficientMarginError`).
- [src/environment/](file:///d:/reverse_indi/src/environment/): Quản lý môi trường và dependency injection:
  - [environment.py](file:///d:/reverse_indi/src/environment/environment.py), [context.py](file:///d:/reverse_indi/src/environment/context.py): Đóng gói context chạy và singleton services.
  - [config.py](file:///d:/reverse_indi/src/environment/config.py): Parser đọc cấu hình YAML/JSON.
  - [registry.py](file:///d:/reverse_indi/src/environment/registry.py): Dynamic Registry đăng ký chiến lược và module.

#### 🔹 **[PHASE 1] Market Data Engine & Feature Engineering**
- [src/market_data/](file:///d:/reverse_indi/src/market_data/): Tải, làm sạch và lưu trữ dữ liệu nến/tick:
  - [loader.py](file:///d:/reverse_indi/src/market_data/loader.py): Interface & DataLoader nến lịch sử.
  - [cleaner.py](file:///d:/reverse_indi/src/market_data/cleaner.py): Xử lý missing bars, lấp chỗ trống timestamp.
  - [dataset.py](file:///d:/reverse_indi/src/market_data/dataset.py), [catalog.py](file:///d:/reverse_indi/src/market_data/catalog.py): Container dữ liệu và danh mục dataset.
  - [versioning.py](file:///d:/reverse_indi/src/market_data/versioning.py): Tính hash MD5 kiểm soát phiên bản dữ liệu.
- [src/features/](file:///d:/reverse_indi/src/features/): Tính toán tính chất kỹ thuật (Causal Features):
  - [feature_engine.py](file:///d:/reverse_indi/src/features/feature_engine.py): Pipeline tính toán features tổng hợp.
  - [indicators.py](file:///d:/reverse_indi/src/features/indicators.py): Thư viện tính ATR Wilder RMA, Swing High/Low.
  - [zones.py](file:///d:/reverse_indi/src/features/zones.py): Dynamic Fibo & Key Zone Registry Engine (`config/zones.yaml`).
  - [causal.py](file:///d:/reverse_indi/src/features/causal.py): Guardrail cưỡng chế shift lag loại bỏ Lookahead Bias.

#### 🔹 **[PHASE 2] Execution Engine**
- [src/execution/](file:///d:/reverse_indi/src/execution/): Mô phỏng thực thi lệnh thực tế & tính phí:
  - [execution_engine.py](file:///d:/reverse_indi/src/execution/execution_engine.py): Orchestrator xử lý luồng order fill.
  - [fill_model.py](file:///d:/reverse_indi/src/execution/fill_model.py): Dual Fill Simulator (**Wick Touch** vs **Bar Close**).
  - [slippage.py](file:///d:/reverse_indi/src/execution/slippage.py): Tính toán trượt giá động theo ATR volatility.
  - [fee_model.py](file:///d:/reverse_indi/src/execution/fee_model.py): Phí hoa hồng Commission (4bps Maker/Taker).
  - [funding.py](file:///d:/reverse_indi/src/execution/funding.py): Phí Funding Rate 8h cho hợp đồng Perp Crypto.
  - [broker.py](file:///d:/reverse_indi/src/execution/broker.py): Interface nối với Broker API thực tế.

#### 🔹 **[PHASE 3] Portfolio Engine**
- [src/portfolio/](file:///d:/reverse_indi/src/portfolio/): Quản trị vị thế và quản lý rủi ro:
  - [account.py](file:///d:/reverse_indi/src/portfolio/account.py): Theo dõi Cash balance, Equity và Margin reserve.
  - [position.py](file:///d:/reverse_indi/src/portfolio/position.py): Quản lý vòng đời vị thế đang mở.
  - [pnl.py](file:///d:/reverse_indi/src/portfolio/pnl.py): Tính toán Realized PnL & Unrealized Mark-to-Market PnL.
  - [margin.py](file:///d:/reverse_indi/src/portfolio/margin.py): Kiểm tra đòn bẩy và tỷ lệ ký quỹ ban đầu.
  - [risk_manager.py](file:///d:/reverse_indi/src/portfolio/risk_manager.py): Tính Lot Sizing chuẩn định lượng: `(Equity * Risk%) / abs(Entry - Stop)`.
  - [allocator.py](file:///d:/reverse_indi/src/portfolio/allocator.py): Phân bổ vốn giữa nhiều chiến lược trong danh mục.

#### 🔹 **[PHASE 4] Backtest Engine & Strategy DSL**
- [src/strategies/](file:///d:/reverse_indi/src/strategies/): Giao diện chiến lược giao dịch:
  - [base.py](file:///d:/reverse_indi/src/strategies/base.py): Class trừu tượng `BaseStrategy` bắt buộc mọi chiến lược kế thừa.
  - [schema.py](file:///d:/reverse_indi/src/strategies/schema.py), [registry.py](file:///d:/reverse_indi/src/strategies/registry.py): Định nghĩa và đăng ký tham số chiến lược.
- [src/backtest/](file:///d:/reverse_indi/src/backtest/): Engine chạy mô phỏng backtest:
  - [engine.py](file:///d:/reverse_indi/src/backtest/engine.py): Backtest Engine tổng hợp.
  - [event_loop.py](file:///d:/reverse_indi/src/backtest/event_loop.py): Causal Event Loop xử lý theo chuỗi sự kiện.
  - [runner.py](file:///d:/reverse_indi/src/backtest/runner.py): Runner hỗ trợ gọi từ CLI script.
  - [splitter.py](file:///d:/reverse_indi/src/backtest/splitter.py): Purged & Embargoed Walk-Forward Splitter (cắt ranh giới Train/Test).

#### 🔹 **[PHASE 5] Evaluation Engine**
- [src/evaluation/](file:///d:/reverse_indi/src/evaluation/): Phân tích hiệu năng & độ bền bỉ chiến lược:
  - [metrics.py](file:///d:/reverse_indi/src/evaluation/metrics.py): Tính Sharpe Ratio, Sortino, Max Drawdown, Win Rate, Expectancy.
  - [cost_analysis.py](file:///d:/reverse_indi/src/evaluation/cost_analysis.py): Phân tích Fee Drag Ratio tác động lên PnL.
  - [robustness/](file:///d:/reverse_indi/src/evaluation/robustness): Đánh giá độ nhạy tham số (Plateau check) & Monte Carlo simulation.
  - [diagnostics/](file:///d:/reverse_indi/src/evaluation/diagnostics): Công cụ xuất đồ thị & Tearsheets.

#### 🔹 **[PHASE 6] 100–1000 Strategy Runner**
- [src/batch/](file:///d:/reverse_indi/src/batch/): Thực thi song song hàng loạt chiến lược:
  - [parallel_runner.py](file:///d:/reverse_indi/src/batch/parallel_runner.py): Điều phối Multi-processing / Ray Worker Pool.
  - [job_schema.py](file:///d:/reverse_indi/src/batch/job_schema.py), [task_queue.py](file:///d:/reverse_indi/src/batch/task_queue.py): Quản lý hàng đợi 100-1000 backtest jobs.
  - [aggregator.py](file:///d:/reverse_indi/src/batch/aggregator.py): Tổng hợp & xếp hạng chiến lược (Rank by Sharpe/Expectancy).

#### 🔹 **[PHASE 7] Strategy Generator**
- [src/generator/](file:///d:/reverse_indi/src/generator/): Tự động sinh cấu trúc chiến lược:
  - [factory.py](file:///d:/reverse_indi/src/generator/factory.py): Khởi tạo chiến lược linh hoạt từ cấu hình JSON/YAML.
  - [grammar.py](file:///d:/reverse_indi/src/generator/grammar.py): Bộ quy tắc ghép mệnh đề DSL (Entry/Exit rules).
  - [blocks.py](file:///d:/reverse_indi/src/generator/blocks.py): Các khối xây dựng (Indicator + Zone Filter + Trigger Signal).
  - [parameter_sampler.py](file:///d:/reverse_indi/src/generator/parameter_sampler.py): Lấy mẫu tham số Optuna Bayesian Sampler.

#### 🔹 **[PHASE 8] Evolution Engine**
- [src/evolution/](file:///d:/reverse_indi/src/evolution/): Tiến hóa chiến lược bằng Thuật toán Di truyền (Genetic Algorithm):
  - [ga_engine.py](file:///d:/reverse_indi/src/evolution/ga_engine.py): Vòng lặp tiến hóa qua N thế hệ (Generations loop).
  - [population.py](file:///d:/reverse_indi/src/evolution/population.py): Quản lý quần thể các bộ gen chiến lược.
  - [operators.py](file:///d:/reverse_indi/src/evolution/operators.py): Phép toán Lai ghép (Crossover) & Đột biến (Mutation).
  - [fitness.py](file:///d:/reverse_indi/src/evolution/fitness.py): Hàm Fitness tổng hợp (Phạt chiến lược thiếu lệnh hoặc Drawdown cao).
  - [selection.py](file:///d:/reverse_indi/src/evolution/selection.py): Phép chọn lọc Tournament Selection / Roulette Wheel.

#### 🔹 **[PHASE 9] Paper Trading Engine**
- [src/paper/](file:///d:/reverse_indi/src/paper/): Chạy giao dịch ảo real-time:
  - [websocket_stream.py](file:///d:/reverse_indi/src/paper/websocket_stream.py): Kết nối luồng dữ liệu WebSocket từ sàn (Binance/Bybit).
  - [order_router.py](file:///d:/reverse_indi/src/paper/order_router.py): Router đẩy lệnh giả lập vào Paper Exchange.
  - [reconciler.py](file:///d:/reverse_indi/src/paper/reconciler.py): Đồng bộ trạng thái vị thế giữa Local Engine và sàn sau mất kết nối.
  - [notifier.py](file:///d:/reverse_indi/src/paper/notifier.py): Gửi cảnh báo tín hiệu qua Telegram / Discord Webhook.
  - [health_monitor.py](file:///d:/reverse_indi/src/paper/health_monitor.py): Giám sát Ping, Latency và trạng thái sống của hệ thống.

---

### 📂 Pipeline Hiện Tại (`src/quant_lab/`)
Các module trong `src/quant_lab/` phục vụ trực tiếp script runner `run_pipeline.py` (Phiên bản 1.0):
- [data_feed.py](file:///d:/reverse_indi/src/data_feed.py): Tải dữ liệu M15, Wilder RMA ATR & Causal Swings.
- [zone_engine.py](file:///d:/reverse_indi/src/zone_engine.py): Dynamic ATR Zone expansion.
- [projection_engine.py](file:///d:/reverse_indi/src/projection_engine.py): Dự phóng Target Zone hình học.
- [state_machine.py](file:///d:/reverse_indi/src/state_machine.py): Quản lý State Machine 5 giai đoạn.
- [atr_ratchet.py](file:///d:/reverse_indi/src/atr_ratchet.py): Fixed Trailing ATR Ratchet exit.
- [execution_simulator.py](file:///d:/reverse_indi/src/execution_simulator.py): Dual fill & Lot Sizing simulator.
- [wfo_splitter.py](file:///d:/reverse_indi/src/wfo_splitter.py): Splitter Walk-Forward Optimization.
- [optimizer.py](file:///d:/reverse_indi/src/optimizer.py): Optuna Plateau Optimizer.
- [alpha_decay.py](file:///d:/reverse_indi/src/alpha_decay.py): Dual-axis Alpha Decay tracker.
- [reporting.py](file:///d:/reverse_indi/src/reporting.py): Xuất báo cáo tổng hợp OOS verdict.
- [run_pipeline.py](file:///d:/reverse_indi/run_pipeline.py): CLI Runner chạy benchmark hoặc Walk-Forward full.

