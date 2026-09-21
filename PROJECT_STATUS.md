# Project Status

## What was done
- Tái tạo thành công chỉ báo VIP Multi-Trend Indicator (khớp số học 99.98% với `indicator_vip.pine`).
- Cập nhật mã nguồn Pine Script v5 hoàn chỉnh tại [tradingview/indicator_vip.pine](file:///d:/reverse_indi/tradingview/indicator_vip.pine) tập trung 100% vào **Cụm 3 Đường Nấc Thang Ở Giữa (3-Line Stepped Trend Ribbon)**:
  * **Đường Trên (Upper Line)**: `tc2`
  * **Đường Giữa (Center Line)**: `tc1` (Đường xu hướng chính dạng nấc thang)
  * **Đường Dưới (Lower Line)**: `tc3`
  * **Cơ chế đổi màu**: Chuyển đồng bộ sang **MÀU XANH LÁ** khi Uptrend và **MÀU ĐỎ** khi Downtrend, kết hợp tô dải nấc thang chuẩn 100% theo ảnh.
- Xây dựng hoàn chỉnh **Pipeline Quant Lab: Fibo Zone-Registry + Projection + ATR Ratchet**:
  - `config/`: Tach biệt `zones.yaml`, `fixed_params.yaml`, `search_space.yaml`.
  - `src/`: Codebase 10 modules sạch theo thiết kế SRP (Data Feed, Zone Engine, Projection Engine, 5-Stage State Machine, Fixed ATR Ratchet Exit, Execution Simulator với risk sizing, Purged WFO Splitter, Optuna Plateau Optimizer, Dual-Axis Alpha Decay Tracker, Reporting Engine).
  - CLI Runner `run_pipeline.py`: Hỗ trợ `--benchmark-trials` và `--n-trials` WFO lab.
- Kiểm thử Benchmark: 20 trials hoàn tất trong **3.92 giây** (~196 ms/trial).
- Xây dựng thành công bộ khung kiến trúc mô-đun hóa **10 Phase (PHASE 0 → PHASE 9)** dưới `src/`:
  - Dựng 14 subpackage (`core`, `environment`, `market_data`, `features`, `execution`, `portfolio`, `strategies`, `backtest`, `evaluation`, `experiments`, `batch`, `generator`, `evolution`, `paper`).
  - Khởi tạo 80 scaffold modules với đầy đủ docstring SRP (`[PURPOSE]`, `[DEPENDENCIES]`, `[ARGS]`, `[RETURNS]`, `[SIDE EFFECTS]`) và type hints.
  - Kiểm thử import 14 package thành công 100% và đảm bảo tính tương thích tuyệt đối với `run_pipeline.py`.
- Cập nhật trọn vẹn [README.md gốc](file:///d:/reverse_indi/README.md) tài liệu hóa chi tiết 4 chiều kiến trúc (**Dimension 1: Correctness**, **Dimension 2: Simplicity**, **Dimension 3: Scalability**, **Dimension 4: Evolvability**) cùng sơ đồ thư mục 10 Phase.
- Dọn dẹp sạch toàn bộ 72 file stub placeholder trong 14 subfolder gói `src/`, chỉ giữ lại `__init__.py` ở mỗi thư mục package để sẵn sàng xây dựng từng module từ đầu theo tư duy **Dimension 1 (Correctness)**.
- Xây dựng hoàn chỉnh gói **Time & Experiment Planning Engine (`src/experiments/`)** phục vụ **Dimension 1 (Correctness)**:
  * [config/experiments/time.yaml](file:///d:/reverse_indi/config/experiments/time.yaml): File cấu hình thời gian người dùng (mode: fixed/rolling/expanding, range, warmup, freeze_anchor).
  * [src/experiments/config.py](file:///d:/reverse_indi/src/experiments/config.py): Parser & Validator `TimeConfig`, quy đổi chuỗi `Duration` (`1y`, `6mo`, `30d`, `200bars`).
  * [src/experiments/window.py](file:///d:/reverse_indi/src/experiments/window.py): Immutable Dataclass `TimeWindow` (`frozen=True`) đảm bảo bất đẳng thức `warmup_start <= execution_start < execution_end` & UTC timezone.
  * [src/experiments/run.py](file:///d:/reverse_indi/src/experiments/run.py): Immutable Dataclass `ExperimentRun` (`frozen=True`) với ID, seed, window.
  * [src/experiments/planner.py](file:///d:/reverse_indi/src/experiments/planner.py): `DatasetRange` (Interface trừu tượng không đọc trực tiếp file storage) & `TimePlanner` (giải quyết `now`, tính window, warmup, kiểm tra biên `PlanningError`, sinh `ExperimentRun[]`).
- Tinh chỉnh trọn vẹn [.gitignore](file:///d:/reverse_indi/.gitignore) chuẩn Python Quant Engine (cho phép push dữ liệu `data/` lên Git theo yêu cầu của user, chỉ ignore `venv`, `__pycache__`, IDE config và system logs).
- Xây dựng hoàn chỉnh **Execution Subsystem (`src/execution/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/execution/order.py](file:///d:/reverse_indi/src/execution/order.py): Enums `OrderSide`, `OrderType`, `OrderStatus` và Dataclass bất biến `Order` (`frozen=True`).
  * [src/execution/fill.py](file:///d:/reverse_indi/src/execution/fill.py): Dataclass bất biến `Fill` (`frozen=True`).
  * [src/execution/result.py](file:///d:/reverse_indi/src/execution/result.py): Container `ExecutionResult` tổng hợp audit trail (fills, avg price, fees, slippage).
  * [src/execution/fill_model.py](file:///d:/reverse_indi/src/execution/fill_model.py): Abstract `FillModel`, `OHLCFillModel` & `LowerTimeframeReplayFillModel` (duyệt nến M1 intrabar xác định chính xác thứ tự SL/TP mà không bị lookahead).
  * [src/execution/slippage.py](file:///d:/reverse_indi/src/execution/slippage.py): `FixedSlippageModel` (bps / ticks) & `VolatilitySlippageModel` (ATR).
  * [src/execution/fee.py](file:///d:/reverse_indi/src/execution/fee.py): `PercentageFeeModel` (Maker/Taker bps).
  * [src/execution/funding.py](file:///d:/reverse_indi/src/execution/funding.py): `PerpetualFundingModel` (phí 8h perp).
  * [src/execution/broker.py](file:///d:/reverse_indi/src/execution/broker.py): `Broker` gateway interface & `HistoricalBroker`.
  * [src/execution/execution_engine.py](file:///d:/reverse_indi/src/execution/execution_engine.py): Orchestrator quản lý lifecycle của Order và bắn `ExecutionEvent` audit log.
  * Unit test suite `tests/execution/`: 12/12 Unit tests **PASS 100%** (`test_order_fill.py`, `test_fill_model.py`, `test_slippage_fee.py`, `test_execution_engine.py`).
- Xây dựng hoàn chỉnh **Portfolio & Accounting Subsystem (`src/portfolio/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/portfolio/exceptions.py](file:///d:/reverse_indi/src/portfolio/exceptions.py): `PortfolioException`, `InsufficientMarginError`, `InvalidPositionError`, `RiskRejectError`.
  * [src/portfolio/account.py](file:///d:/reverse_indi/src/portfolio/account.py): Dataclass bất biến `Account` (`initial_capital`, `balance`, `realized_pnl`, `fees_paid`, `funding_paid`, `equity`).
  * [src/portfolio/position.py](file:///d:/reverse_indi/src/portfolio/position.py): Enum `PositionSide` (`LONG`, `SHORT`) và Dataclass bất biến `Position` (enforces `quantity > 0` tuyệt đối, không bao giờ dùng `quantity = -1`).
  * [src/portfolio/pnl.py](file:///d:/reverse_indi/src/portfolio/pnl.py): Pure PnL formulas (`calculate_unrealized_pnl`, `calculate_realized_pnl`).
  * [src/portfolio/margin.py](file:///d:/reverse_indi/src/portfolio/margin.py): `MarginModel`, `SimpleMarginModel` (`position_notional`, `initial_margin`, `used_margin`, `available_margin`).
  * [src/portfolio/risk_manager.py](file:///d:/reverse_indi/src/portfolio/risk_manager.py): `RiskManager` pre-execution guardrail validator (`allow_short`, `max_position_size`, `max_notional`, `max_leverage`).
  * [src/portfolio/portfolio_state.py](file:///d:/reverse_indi/src/portfolio/portfolio_state.py): Snapshot bất biến `PortfolioState`.
  * [src/portfolio/portfolio.py](file:///d:/reverse_indi/src/portfolio/portfolio.py): Class orchestrator `Portfolio` (`apply_fill` xử lý 5 vòng đời vị thế: Open, Increase weighted avg, Reduce, Close, và Reversal 2-step; `mark_to_market`, chống duplicate fill).
  * Unit test suite `tests/portfolio/`: 14/14 Unit tests **PASS 100%** (`test_account_pnl.py`, `test_position_lifecycle.py`, `test_margin_risk.py`, `test_portfolio_integration.py`).
- Xây dựng hoàn chỉnh **Market & Dataset Subsystem (`src/market_data/`)** phục vụ **Dimension 1 (Correctness)**:
  * [config/datasets/](file:///d:/reverse_indi/config/datasets/): Các tệp cấu hình YAML khai báo dataset ([`btcusdt_binance_perp_15m.yaml`](file:///d:/reverse_indi/config/datasets/btcusdt_binance_perp_15m.yaml), [`btcusdt_binance_perp_1m.yaml`](file:///d:/reverse_indi/config/datasets/btcusdt_binance_perp_1m.yaml)) giúp cấu hình linh hoạt thị trường, timeframe, đường dẫn storage (`data/raw/binance/BTCUSDT/...`), version và range mà không cần hard-code.
  * [src/market_data/exceptions.py](file:///d:/reverse_indi/src/market_data/exceptions.py): `MarketDataException`, `InvalidMarketError`, `InvalidDatasetError`, `CatalogError`, `DatasetNotFoundError`, `DuplicateDatasetError`, `DataValidationError`, `IncompatibleDatasetError`.
  * [src/market_data/market.py](file:///d:/reverse_indi/src/market_data/market.py): Dataclass bất biến `Market` (`venue`, `symbol`, `market_type`, `quote_currency`, property `identity`).
  * [src/market_data/timeframe.py](file:///d:/reverse_indi/src/market_data/timeframe.py): Enum `Timeframe` (`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`) hỗ trợ serialization chuẩn dạng chuỗi (`"15m"`) và quy đổi phút/giây.
  * [src/market_data/dataset.py](file:///d:/reverse_indi/src/market_data/dataset.py): Dataclasses bất biến `DataRange`, `StorageReference`, `Dataset` (hỗ trợ `Dataset.from_yaml` / `to_yaml`, `identity -> dataset_id:v3`).
  * [src/market_data/versioning.py](file:///d:/reverse_indi/src/market_data/versioning.py): Engine tính toán SHA-256 content hash deterministic (`calculate_content_hash`, `verify_dataset_hash`).
  * [src/market_data/catalog.py](file:///d:/reverse_indi/src/market_data/catalog.py): Registry `DatasetCatalog` (`register`, `get`, `exists`, `list`, `list_versions`, `load_from_file`, `load_from_dir`).
  * [src/market_data/loader.py](file:///d:/reverse_indi/src/market_data/loader.py): `DatasetLoader` và container `MarketData` (đọc Parquet/CSV, validate UTC timestamp, OHLC bounds, content hash, detect missing candles).
  * [src/market_data/compatibility.py](file:///d:/reverse_indi/src/market_data/compatibility.py): Hàm `validate_compatible_datasets(strategy_ds, execution_ds)`.
  * Unit test suite `tests/market_data/`: 30/30 Unit tests **PASS 100%** (`test_market.py`, `test_dataset.py`, `test_versioning_hash.py`, `test_catalog.py`, `test_loader_validation.py`, `test_compatibility.py`, `test_integration.py`).
- Xây dựng hoàn chỉnh **Config Layer Subsystem (`src/config/` & `config/*.yaml`)** phục vụ **Dimension 1 (Correctness)**:
  * Structure `config/*.yaml` phẳng & sạch sẽ ([`default.yaml`](file:///d:/reverse_indi/config/default.yaml), [`datasets.yaml`](file:///d:/reverse_indi/config/datasets.yaml), [`execution.yaml`](file:///d:/reverse_indi/config/execution.yaml), [`portfolio.yaml`](file:///d:/reverse_indi/config/portfolio.yaml), [`experiments.yaml`](file:///d:/reverse_indi/config/experiments.yaml), [`search.yaml`](file:///d:/reverse_indi/config/search.yaml)): Đã dọn dẹp các thư mục con rỗng/dư thừa để chuẩn hóa cây cấu hình theo đúng kiến trúc MVP.
  * [src/config/exceptions.py](file:///d:/reverse_indi/src/config/exceptions.py): `ConfigError`, `ConfigFileNotFoundError`, `ConfigParseError`, `ConfigValidationError`, `ConfigReferenceError`, `ConfigCompatibilityError`.
  * [src/config/models.py](file:///d:/reverse_indi/src/config/models.py): Typed Dataclasses bất biến (`DefaultEnvConfig`, `DatasetRefConfig`, `ExecutionConfig`, `PortfolioConfig`, `ExperimentTimeConfig`, `ExperimentConfig`).
  * [src/config/validation.py](file:///d:/reverse_indi/src/config/validation.py): Validation engine `validate_experiment_config(exp_config)`.
  * [src/config/loader.py](file:///d:/reverse_indi/src/config/loader.py): Class `ConfigLoader` (`load_default_env`, `load_dataset`, `load_execution`, `load_portfolio`, `load_experiment`, `snapshot_experiment`).
  * Unit test suite `tests/config/`: 19/19 Unit tests **PASS 100%** (`test_loader.py`, `test_models.py`, `test_references.py`, `test_validation.py`, `test_reproducibility.py`).
- Xây dựng hoàn chỉnh **Core Subsystem (`src/core/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/core/exceptions.py](file:///d:/reverse_indi/src/core/exceptions.py): Root base exception `QuantSystemError`.
  * [src/core/types.py](file:///d:/reverse_indi/src/core/types.py): Strict UTC temporal validation (`validate_utc_timestamp`, `create_utc_timestamp`) và primitive aliases (`Symbol`, `Price`, `Quantity`).
  * [src/core/ids.py](file:///d:/reverse_indi/src/core/ids.py): Immutable ID wrappers (`BaseId`, `ExperimentId`, `RunId`, `StrategyId`, `OrderId`, `FillId`, `DatasetId`, `EventId`) hỗ trợ `generate()`.
  * [src/core/clock.py](file:///d:/reverse_indi/src/core/clock.py): Protocol `Clock`, `HistoricalClock` (cho simulation replay với bất đẳng thức `advance_to(t)` không lùi thời gian), và `RealtimeClock` (UTC now).
  * [src/core/events.py](file:///d:/reverse_indi/src/core/events.py): Dataclass bất biến `Event` (`event_id`, `timestamp` UTC, `sequence` deterministic sorting).
  * Unit test suite `tests/core/`: 15/15 Unit tests **PASS 100%** (`test_exceptions.py`, `test_types.py`, `test_ids.py`, `test_clock.py`, `test_events.py`).

- Xây dựng hoàn chỉnh **Environment Subsystem (`src/environment/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/environment/exceptions.py](file:///d:/reverse_indi/src/environment/exceptions.py): `EnvironmentError`, `EnvironmentConstructionError`, `MissingDependencyError`, `EnvironmentValidationError`.
  * [src/environment/registry.py](file:///d:/reverse_indi/src/environment/registry.py): Container `Registry` (`register`, `get`, `contains`, `require`) cách ly 100% không dùng global singletons.
  * [src/environment/environment.py](file:///d:/reverse_indi/src/environment/environment.py): Frozen Dataclass `Environment` (`clock`, `market_data`, `execution`, `portfolio`, `config`, `registry`).
  * [src/environment/context.py](file:///d:/reverse_indi/src/environment/context.py): Frozen Dataclass `ExecutionContext` (`clock`, `run`, `dataset_id`, `execution_id`).
  * [src/environment/factory.py](file:///d:/reverse_indi/src/environment/factory.py): Engine `EnvironmentFactory.create(config, clock, market_data, execution_engine, portfolio)` lắp ghép runtime world hoàn chỉnh.
  * Unit test suite `tests/environment/`: 11/11 Unit tests **PASS 100%** (`test_exceptions.py`, `test_registry.py`, `test_environment.py`, `test_context.py`, `test_factory.py`, `test_integration.py`).
  * Tổng số unit test toàn hệ thống: **114/114 tests PASS 100%** qua 7 subsystem hoàn tất (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11).

## What's next
- Tiếp tục xây dựng các module tiếp theo của **Dimension 1 (Correctness)**:
  1. `backtest/`: `BacktestEngine`, `EventLoop`, `Runner`, `BacktestResult`.
  2. Tích hợp end-to-end pipeline: `Strategy -> Order -> RiskManager -> ExecutionEngine -> Fill -> Portfolio -> PortfolioState -> BacktestResult`.
  3. Xây dựng module `evaluation/` & `strategies/`.

## Open issues / Notes
- None. Toàn bộ 7 subsystem nền tảng (`core`, `config`, `market_data`, `experiments`, `execution`, `portfolio`, `environment`) hoạt động độc lập và liên kết chặt chẽ.
