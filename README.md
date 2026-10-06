# Reverse Engineering VIP Multi-Trend Indicator & Pipeline Quant Lab

Dự án nghiên cứu, tái tạo (reverse-engineer) thuật toán chỉ báo đa xu hướng (VIP Trend Indicator) và xây dựng **Pipeline Quant Lab** hoàn chỉnh cho BTCUSDT M15 theo mô hình **Single Source of Truth (SSOT)** và **Architecture Guardrails**.

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

2. **Core Subsystems (`src/`)**:
   - **`src/config/`**: Config loader, Typed Config Models, Validation.
   - **`src/data/`**: Causal DataLoader, Catalog & SHA-256 Versioning, Dataset, Timeframe & UTC Timestamp Helpers.
   - **`src/features/`**: Indicator features & registry (Wilder RMA ATR, Causal Swings, Zones).
   - **`src/strategies/`**: Strategy Contract (`StrategyContext`, `SignalAction`, `Signal`), reference strategy (`EMAStrategy`). Không phụ thuộc vào `trading`.
   - **`src/trading/`**:
     - `execution/`: Mô phỏng khớp lệnh, quản lý Order/Fill, historical broker, fill models, slippage, fees, funding, execution engine.
     - `portfolio/`: Quản lý tài khoản (`Account`), vị thế (`Position`), Margin, PnL, Portfolio orchestrator & pre-execution risk guard (`RiskManager`).
     - `backtest.py`: Causal T+1 backtest loop orchestrator (`BacktestEngine`), `HistoricalClock`, `Clock`, `BacktestResult`, `EnvironmentFactory`, `run_trade_simulation`.
   - **`src/experiments/`**: TimePlanner, TimeWindow, ExperimentRun, Purged WFO Splitter, Optuna Bayesian Optimizer.
   - **`src/evaluation/`**: Đánh giá chỉ số định lượng (`BasicMetrics`), Alpha decay 2 trục & reporting export.

3. **CLI Runners**:
   - Strict Production Backtest: `.\venv\Scripts\python.exe run_backtest.py --dataset-definition <dataset.yaml> --fast-period 20 --slow-period 50`
   - Pipeline Benchmark: `.\venv\Scripts\python.exe run_pipeline.py --benchmark-trials 5`
   - Unit Test Discovery: `.\venv\Scripts\python.exe -m unittest discover -s tests`

---

## 3. Triết Lý Thiết Kế 4 Chiều (4-Dimension Engineering Framework)

Hệ thống được phát triển theo định hướng kiến trúc 4 chiều nghiêm ngặt:

1. **Dimension 1 — Correctness (Tập trung tối thượng)**:
   - Tất cả module cốt lõi được bảo vệ bằng ranh giới phụ thuộc 1 chiều (DAG Matrix).
   - **Mục tiêu tối thượng**: `same config + same dataset + same seed = same result` (100% Deterministic & Reproducible).
2. **Dimension 2 — Simplicity (Tinh gọn kiến trúc)**:
   - Kiến trúc phẳng chuẩn 3-tier: `Research (data, config, features, strategies)` -> `Trading Engine (trading/execution, trading/portfolio, trading/backtest)` -> `Evaluation (experiments, evaluation)`.
   - Mỗi responsibility chỉ có đúng một Single Source of Truth (SSOT), loại bỏ rác/wrapper/pass-through legacy layers.
3. **Dimension 3 — Scalability (Mở rộng quy mô từng bước)**:
   - Phân hệ `src/trading/` chia nhỏ thành `execution/`, `portfolio/`, và `backtest.py` cho phép mở rộng thuật toán độc lập mà không làm ảnh hưởng đến các phân hệ khác.
4. **Dimension 4 — Evolvability (Khả năng tiến hóa không phá vỡ Core)**:
   - `strategies` hoàn toàn độc lập với `trading`, cho phép mở rộng chiến lược vô hạn mà không sợ rò rỉ khớp lệnh hay vị thế.

---

## 4. Cấu Trúc Thư Mục Hệ Thống (Consolidated Architecture Map)

```text
quant_lab/
├── config/                     # File cấu hình YAML hệ thống (default, datasets, execution, portfolio, experiments)
├── data/                       # Dữ liệu nến & tick lịch sử (CSV/Parquet)
├── docs/                       # Tài liệu thiết kế & Yêu cầu tính năng (requirements/ REQ-*.md)
├── reports/                    # Output báo cáo định lượng (Walk-Forward OOS, Alpha Decay, JSON/Markdown)
├── scripts/                    # Script CLI tiện ích (verification, reconstruction)
├── tests/                      # Suite 115 Unit & Architecture tests
├── tradingview/                # Mã nguồn Pine Script v5 chỉ báo VIP (indicator_vip.pine)
└── src/                        # Mã nguồn Python chính
    ├── config/                 # Config loader, Typed Config Models, Validation
    ├── data/                   # Market, Dataset, Catalog, Loader, SHA-256 Versioning, BaseId, UTC Timestamp Helpers
    ├── features/               # Causal Feature Engineering & Indicator Registry (ATR, Swings, Zones)
    ├── strategies/             # Strategy DSL Contract, Signal, StrategyId, StrategyContext, EMA Reference Strategy
    ├── trading/                # Trading Subsystem
    │   ├── execution/          # Order, Fill, Broker, ExecutionEngine, FillModel, Slippage, Fees, Funding
    │   ├── portfolio/          # Account, Position, PositionSide, PnL, Margin, Risk, Portfolio
    │   └── backtest.py         # BacktestEngine, HistoricalClock, Clock, BacktestResult, EnvironmentFactory, Simulator
    ├── experiments/            # TimePlanner, TimeWindow, TimeConfig, ExperimentRun, Splitter, Optuna Optimizer
    └── evaluation/             # BasicMetrics, Alpha Decay Analysis, Reporting
```

---

## 5. Quy Trình Kiểm Thử & Verification

```bash
# 1. Chạy toàn bộ 115 unit tests
.\venv\Scripts\python.exe -m unittest discover -s tests

# 2. Kiểm tra Golden Behavioral Baseline (Yêu cầu khớp số học 100.0000%)
.\venv\Scripts\python.exe run_backtest.py --dataset-definition <dataset.yaml> --fast-period 20 --slow-period 50
```
