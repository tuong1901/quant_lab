# Project Status

## 2026-10-21 — strict runner wiring and function logs
- Done: configured ATR period reaches the indicator; clock/context use selected dataset; explicit engine symbol is separate from run identity. Existing callers retain the run-ID symbol fallback.
- Done: finite numeric validation and risk-free-rate bounds; INFO runtime summaries and DEBUG function traces; CLI appends UTF-8 logs to `logs/backtest.log` and keeps reports on stdout.
- Verification: 3 config tests + 8 synthetic runner/engine/logging tests passed. No real YAML, market data or log files were accessed by these tests.
- Next/open: real-data E2E awaits separate file-read permission; legacy config tests still reference retired YAML and outdated types. Existing ATR initialization and fill-bar ATR timing warrant a separate causality review; unchanged by this wiring repair.
- REQ: `docs/requirements/REQ-20261021-fix-backtest-wiring-and-logging.md`.

## Done
- REQ: `docs/requirements/REQ-20261006-remove-legacy-config-yaml.md` (legacy YAML retired). Removed the ten user-approved files and `tests/config/test_loader.py`; strict `backtest.yaml` and `config/datasets/` descriptors remain.
- REQ: `docs/requirements/REQ-20261006-strict-backtest-risk-configuration.md` (in progress). Strict `backtest.yaml` now configures capital/leverage, risk sizing, ATR stop/2R target, fees, and slippage. Parser check and 20 portfolio/evaluation regressions pass; real-data strict E2E remains pending data-read approval.
- REQ: `docs/requirements/REQ-20261006-strict-backtest-runner.md` (strict CLI runner completed; 3 runner/data E2E tests passed). `run_backtest.py` now follows Dataset YAML → Loader → EMA features → EMAStrategy → BacktestEngine → unified evaluation; legacy WFO remains only in `run_pipeline.py`.
- REQ: `docs/requirements/REQ-20261006-evaluation-accounting-reconciliation.md` (completed). Strict runner output reconciles initial capital, realized PnL, fees, funding, account equity, unrealized PnL, final equity, and residual.
- REQ: `docs/requirements/REQ-20261006-evaluation-kernel-and-trade-ledger.md` (Phase A completed: 13 unit tests and strict E2E passed). Evaluation now exposes timeframe-aware CAGR, max drawdown, volatility, Sharpe, Sortino, and Calmar from equity snapshots; trade-ledger metrics remain future work.
- REQ: `docs/requirements/REQ-20261005-continuity-high-repair.md` (16 data contract tests and E2E passed). Continuity cleaning touches only discontinuous opens; a candidate open above high is clamped back to the existing high, never changing high.
- REQ: `docs/requirements/REQ-20261005-e2e-data-to-evaluation.md` (strict Dataset → Feature → Strategy → Backtest → BasicMetrics passed on 34 valid real M15 candles). Result: 10 orders/fills, final equity $9,343.56, net PnL -$656.44 (-6.564396%), 9 realized trade events, 22.22% win rate.
- REQ: `docs/requirements/REQ-20261005-portfolio-contract-tests.md` (P0 portfolio contracts passed: 14 test methods covering all 18 contract IDs).
- Portfolio lifecycle/accounting is covered for open/add/reduce/close/reversal, PnL signs, fees, MTM, equity reconciliation, duplicate fills, and the golden lifecycle; no production defect was found.
- REQ: `docs/requirements/REQ-20261005-execution-contract-tests.md` (targeted execution contract suite passed: 9 tests).
- Execution engine now separates order eligibility/reference pricing from market slippage and fee calculation. Market fills remain T+1 Open (fallback Close); touched limit orders fill exactly at their submitted limit price and cannot double fill.
- Execution T+1 demo backtest passed: order at 10:15 UTC filled once at the 10:30 UTC open (105.00), final equity 10,004.96. Legacy timing regression tests are blocked before execution by a legacy dataset storage-format value incompatible with the strict data contract.
- REQ: `docs/requirements/REQ-20261005-data-contract-strict-pipeline.md`.
- Strict data contract now enforces canonical UTC timestamps, `[start, end)`, full market identity, canonical SHA-256, OHLCV bounds, and strict no-gap loading.
- Canonicalization now aligns each non-initial candle open to the preceding close before hash/validation; invalid corrected OHLC ranges remain rejected.
- Targeted contract + real-data E2E suite: 13 tests passing; dedicated mutation test passes. Production CLI now requires YAML Dataset descriptors.

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

- Xây dựng hoàn chỉnh **Strategy Contract Subsystem (`src/strategies/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/strategies/exceptions.py](file:///d:/reverse_indi/src/strategies/exceptions.py): `StrategyError`, `InvalidSignalError`, `StrategyContextError`.
  * [src/strategies/signal.py](file:///d:/reverse_indi/src/strategies/signal.py): Enum `SignalAction` (`HOLD`, `LONG`, `SHORT`) và Frozen Dataclass `Signal` (`timestamp`, `action`, `strategy_id`, `metadata`).
  * [src/strategies/context.py](file:///d:/reverse_indi/src/strategies/context.py): Read-only Frozen Dataclass `StrategyContext` (`timestamp`, `price`, `position_side`, `features`).
  * [src/strategies/strategy.py](file:///d:/reverse_indi/src/strategies/strategy.py): Protocol Contract `Strategy` (`@runtime_checkable`) định nghĩa `on_bar(context) -> Signal`.
  * [src/strategies/ema.py](file:///d:/reverse_indi/src/strategies/ema.py): Reference Strategy `EMAStrategy` (`EMA20 > EMA50 -> LONG`, `EMA20 < EMA50 -> SHORT`, equal/missing -> `HOLD`).
  * Unit test suite `tests/strategies/`: 10/10 Unit tests **PASS 100%** (`test_exceptions.py`, `test_signal.py`, `test_context.py`, `test_strategy_contract.py`, `test_ema_strategy.py`).
  * Tổng số unit test toàn hệ thống: **124/124 tests PASS 100%** qua 8 subsystem hoàn tất (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10).

- Xây dựng hoàn chỉnh **Backtest Engine Subsystem (`src/backtest/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/backtest/exceptions.py](file:///d:/reverse_indi/src/backtest/exceptions.py): `BacktestError`, `BacktestExecutionError`, `InvalidSimulationStateError`.
  * [src/backtest/state.py](file:///d:/reverse_indi/src/backtest/state.py): Dataclass `BacktestState` (`current_timestamp`, `bars_processed`, `signals`, `orders`, `fills`, `portfolio_states`).
  * [src/backtest/result.py](file:///d:/reverse_indi/src/backtest/result.py): Frozen Dataclass `BacktestResult` (`run_id`, `strategy_id`, `dataset_id`, `initial_capital`, `bars_processed`, `final_timestamp`, `signals`, `orders`, `fills`, `portfolio_history`, `final_portfolio`).
  * [src/backtest/engine.py](file:///d:/reverse_indi/src/backtest/engine.py): Simulation Loop Orchestrator `BacktestEngine` (`run(df) -> BacktestResult` với hỗ trợ `HistoricalClock`, cửa sổ Warmup vs Execution, dịch `Signal -> Order`, đẩy lệnh tới `ExecutionEngine`, khớp `Fill` vào `Portfolio`, và `mark_to_market`).
  * Unit test suite `tests/backtest/`: 9/9 Unit tests **PASS 100%** (`test_exceptions.py`, `test_state.py`, `test_result.py`, `test_engine.py`).
  * Tổng số unit test toàn hệ thống: **133/133 tests PASS 100%** qua 9 subsystem hoàn tất (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10, `backtest`: 9).

- Xây dựng hoàn chỉnh **Basic Metrics Subsystem (`src/evaluation/`)** phục vụ **Dimension 1 (Correctness)**:
  * [src/evaluation/exceptions.py](file:///d:/reverse_indi/src/evaluation/exceptions.py): Base exceptions `EvaluationError` kế thừa `QuantSystemError`, và `InvalidEvaluationError` (raised khi `initial_capital <= 0`).
  * [src/evaluation/metrics.py](file:///d:/reverse_indi/src/evaluation/metrics.py): Dataclass bất biến `BasicMetrics` (`initial_capital`, `final_equity`, `net_pnl`, `return_pct`, `realized_pnl`, `total_fees`, `trade_count`, `win_rate`, `equity_curve`) và hàm thuần `calculate_basic_metrics(result)` / `BasicMetrics.from_result(result)`.
  * [src/evaluation/README.md](file:///d:/reverse_indi/src/evaluation/README.md): Tài liệu hóa cấu trúc module, nguyên tắc thiết kế read-only, công thức tính toán và hướng dẫn sử dụng.
  * Unit test suite `tests/evaluation/`: 4/4 Unit tests **PASS 100%** (`test_exceptions.py`, `test_metrics.py`).
  * Tổng số unit test toàn hệ thống: **137/137 tests PASS 100%** qua 10 subsystem hoàn tất (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10, `backtest`: 9, `evaluation`: 4).

- Thực hiện hoàn chỉnh **Forensic Environment & Backtest Integrity Audit**:
  * [tests/audit/test_integrity.py](file:///d:/reverse_indi/tests/audit/test_integrity.py): Bổ sung unit tests kiểm tra timing execution, same-bar lookahead, HOLD-only sanity, alternating signals, random strategy determinism, và boundary execution windows.
  * [tests/audit/test_scenarios.py](file:///d:/reverse_indi/tests/audit/test_scenarios.py): Bổ sung 6 kịch bản thử nghiệm tổng hợp (Scenario A đến F: LONG profit, LONG loss, SHORT profit, SHORT loss, Reversal, Open position end).
  * [tests/audit/test_reconciliation.py](file:///d:/reverse_indi/tests/audit/test_reconciliation.py): Reconcile 3 giao dịch thực nghiệm bằng tay độc lập và xác minh đẳng thức kế toán ($Initial + Realized + Unrealized - Fees == Final Equity$).
  * Tổng số unit test toàn hệ thống: **152/152 tests PASS 100%** qua 11 package test modules (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10, `backtest`: 9, `evaluation`: 4, `audit`: 15).

- Đã khắc phục hoàn chỉnh lỗ hổng **Backtest Execution Timing / Look-Ahead Bug**:
  * [src/backtest/engine.py](file:///d:/reverse_indi/src/backtest/engine.py): Đổi thứ tự vòng lặp nến trong `BacktestEngine.run()` để `ExecutionEngine.process_market_data()` xử lý các lệnh chờ từ các nến trước ($T-1$) ở đầu nến $T$ trước, sau đó mới cho `Strategy.on_bar()` quan sát giá Close nến $T$ và sinh lệnh mới cho nến $T+1$.
  * [tests/audit/test_timing_fix.py](file:///d:/reverse_indi/tests/audit/test_timing_fix.py): Bộ kiểm thử hồi quy thời gian với các assertion bắt buộc (`fill.timestamp > order.created_at`, `fill.timestamp == bar_T_plus_1_timestamp`, `fill.price == open_T_plus_1`).
  * Tổng số unit test toàn hệ thống: **156/156 tests PASS 100%** qua 11 package test modules (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10, `backtest`: 9, `evaluation`: 4, `audit`: 19).

- Thực hiện hoàn chỉnh **Full Experimental Environment Integrity Audit** theo 15 vùng cơ học & tính lặp lại:
  * [tests/audit/test_env_integrity.py](file:///d:/reverse_indi/tests/audit/test_env_integrity.py): Bổ sung unit tests kiểm thử Risk-Sizing Trace (Case A & B), Perpetual Funding Model, và State Isolation giữa các Environment độc lập.
  * Lập báo cáo kiểm thử môi trường chi tiết tại [env_audit_report.md](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/env_audit_report.md).
  * Trạng thái chứng nhận môi trường: **NO (NOT VERIFIED)** do các vấn đề cần khắc phục trước khi test strategy: `AUDIT-RISK-01` (Risk-Sizing theo Stop Loss chưa được nạp/áp dụng), `AUDIT-CFG-01` (Bất đồng comment & config phí), `AUDIT-FUND-01` (Vòng lặp funding 8h chưa tích hợp vào BacktestEngine).
  * Tổng số unit test toàn hệ thống: **156/156 tests PASS 100%** qua 11 package test modules (`core`: 15, `config`: 19, `market_data`: 30, `experiments`: 14, `execution`: 12, `portfolio`: 14, `environment`: 11, `strategies`: 10, `backtest`: 9, `evaluation`: 4, `audit`: 19).
- Viết lại trọn vẹn và chuẩn hóa toàn bộ [src/README.md](file:///d:/reverse_indi/src/README.md) thành Catalog Mã Nguồn Toàn Diện:
  * Liệt kê chi tiết toàn bộ các file nguồn thuộc 14 packages bên dưới `src/`.
  * Mô tả chức năng, các lớp (classes), các hàm (functions), tham số đầu vào (`[ARGS]`), giá trị đầu ra (`[RETURNS]`), sự phụ thuộc (`[DEPENDENCIES]`) và tác động hệ thống (`[SIDE EFFECTS & IMPACT]`).
  * Xây dựng ma trận phụ thuộc hướng 1 chiều (DAG Dependency Matrix) và sơ đồ luồng dữ liệu (Data Flow Diagram) chuẩn hóa mối liên kết giữa các module trong hệ thống.
  * Tích hợp tài liệu hướng dẫn chạy 115 test cases (bao gồm Mutation Campaign v2).
- Xây dựng **Sơ đồ Kiến trúc Hệ thống Master & Mã Draw.io (`system_architecture.drawio`)**:
  * Đã tổng hợp toàn bộ 8 cụm module (`src/backtest`, `src/core`, `src/environment`, `src/market_data`, `src/features`, `src/strategies`, `src/portfolio`, `src/execution`) và quy tắc biên kiến trúc DAG vào một sơ đồ thống nhất.
  * Đã tạo file mã nguồn Draw.io XML chuẩn tại [system_architecture.drawio](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/system_architecture.drawio) và tài liệu tổng hợp tại [drawio_system_architecture.md](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/drawio_system_architecture.md).
- Xây dựng **Chi Tiết Phân Hệ 1 (`src/core/`) - Mã Bản Vẽ Draw.io Dành Riêng & Báo Cáo Input/Output Kỳ Vọng**:
  * Đã xuất file Draw.io dành riêng cho Phân hệ 1 tại [subsystem_1_core.drawio](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/subsystem_1_core.drawio) và tài liệu phân tích chi tiết tại [subsystem_1_core_guide.md](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/subsystem_1_core_guide.md).
  * Phân tích chi tiết 100% tất cả các file (`types.py`, `clock.py`, `ids.py`, `events.py`, `exceptions.py`), từng hàm, Input/Output thực tế, Input/Output kỳ vọng (Contract) và ví dụ minh họa trực quan.

- Xây dựng **Bộ Bản Vẽ Draw.io Đa Trang Chi Tiết Cho Tất Cả 8 Phân Hệ (`subsystems_architecture.drawio`)**:
  * Đã xuất file Draw.io 9 trang/tabs tại [subsystems_architecture.drawio](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/subsystems_architecture.drawio) và hướng dẫn chi tiết tại [drawio_all_subsystems_guide.md](file:///C:/Users/tuong.hc/.gemini/antigravity-ide/brain/89950be9-e28c-470c-903c-190039046923/drawio_all_subsystems_guide.md), cho phép người dùng mở từng tab sơ đồ riêng biệt cho từng phân hệ trong Draw.io.
- Xây dựng **Cẩm Nang Chi Tiết Logic Hoạt Động & Kịch Bản Test Case Từng File (`module_catalog_deep_dive.md`)**:
  * Liệt kê và phân tích toàn bộ 8 phân hệ trong `src/` qua 4 góc nhìn: Ngôn ngữ Kinh doanh/Đời thực, Thông số Kỹ thuật Chi tiết (Hàm, inputs, outputs, side effects), Mối quan hệ giữa các Folder, và Kịch bản Viết Unit Test gợi ý giúp người dùng tự gõ testcase cho từng file.

- Thực hiện thành công bài task Hợp nhất & Chuẩn hóa Kiến trúc Tinh gọn 6 Khối Physical Domain theo [REQ-20261001-architecture-reorganization.md](file:///d:/reverse_indi/docs/requirements/REQ-20261001-architecture-reorganization.md):
  * **Hợp nhất 6 Physical Domain Folders**: Tinh gọn thư mục `src/` và `tests/` thành 6 Domain Folders chuẩn (`data`, `environment`, `features`, `strategies`, `engine`, `evaluation`) cùng `core`, `config`, `experiments`. Xóa bỏ hoàn toàn các folder rỗng (`batch`, `generator`, `evolution`, `paper`, `market_data`, `portfolio`, `execution`, `backtest`).
  * **Xóa 100% Legacy Flat Files**: Xóa sạch các file flat cũ. Mã nguồn hiện tại tập trung 100% tại Single Source of Truth (`src/<domain>/`).
  * **Khắc phục `VIOLATION-01`**: Di chuyển Enum `PositionSide` về `src/core/types.py`. Bộ kiểm thử tĩnh DAG layer `test_dependency_direction.py` đạt **PASS 100%**.
  * **Toàn bộ Unit Test Suite PASS 100%**: Tất cả **115/115 unit tests** trong thư mục `tests/` chạy thành công **100% OK**.
  * **Golden Behavioral Baseline Verification**: Chạy kiểm tra so sánh với snapshot `golden_baseline_v1.json` đạt **PASSED 100.0000% NUMERICAL MATCH** (103/103 trades khớp chính xác tuyệt đối từng số thập phân, Final Equity = $11,812.54).
  * **Pine Script Reconstruction Verification**: Chạy `scripts/validate_reconstruction.py` xác minh độ chính xác 99.9884%.
  * Lập báo cáo nghiệm thu kiến trúc chi tiết tại [docs/architecture_certification_report.md](file:///d:/reverse_indi/docs/architecture_certification_report.md) và audit simplification tại [docs/architecture_simplification_audit.md](file:///d:/reverse_indi/docs/architecture_simplification_audit.md).
- Thực hiện thành công bài task Chia nhỏ Sub-package cho `src/engine/` và `src/environment/` theo [REQ-20261002-engine-subfolder-organization.md](file:///d:/reverse_indi/docs/requirements/REQ-20261002-engine-subfolder-organization.md):
  * **Tách Sub-package Single Responsibility**: Tách `src/engine/` thành 3 sub-packages (`execution/`, `models/`, `backtest/`) và `src/environment/` thành 2 sub-packages (`accounting/`, `runtime/`).
  * **100% Backward-Compatible Re-exports**: `src/engine/__init__.py` và `src/environment/__init__.py` re-export đầy đủ các public symbols.
  * **Toàn bộ Unit Test Suite PASS 100%**: 115/115 unit tests vượt qua 100%.
  * **Golden Baseline Verification**: `run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` đạt **PASSED 100.0000% NUMERICAL MATCH**.

- Thực hiện thành công bài task Cập nhật toàn bộ tài liệu Catalog Kiến trúc theo [REQ-20261002-update-readme-architecture.md](file:///d:/reverse_indi/docs/requirements/REQ-20261002-update-readme-architecture.md):
  * **Cập nhật Root [README.md](file:///d:/reverse_indi/README.md)**: Phản ánh sơ đồ cây 6 Physical Domains chuẩn hóa cùng cấu trúc sub-packages mới của `engine` và `environment`.
  * **Cập nhật Master Source Catalog [src/README.md](file:///d:/reverse_indi/src/README.md)**: Liệt kê chi tiết 100% tất cả các file nguồn, lớp, hàm, tham số đầu vào (`[ARGS]`), giá trị đầu ra (`[RETURNS]`), phụ thuộc (`[DEPENDENCIES]`), tác động hệ thống (`[SIDE EFFECTS & IMPACT]`), đường dẫn file chuẩn markdown link (`file:///...`) và ma trận phụ thuộc hướng DAG.

- Thực hiện thành công bài task Giải thể hoàn toàn thư mục `src/core/` và Phân bổ lại về các Domain Owners theo [REQ-20261002-dissolve-core-folder.md](file:///d:/reverse_indi/docs/requirements/REQ-20261002-dissolve-core-folder.md):
  * **Giải thể `src/core/` 100%**: Xóa bỏ hoàn toàn folder `src/core/` giúp kiến trúc gọn gàng, trực quan và không có lớp trừu tượng dư thừa.
  * **Phân bổ về đúng Domain Owner**: `PositionSide` $\rightarrow$ `src/environment/accounting/position.py`; `OrderSide`, `OrderId`, `FillId`, `Event` $\rightarrow$ `src/engine/execution/order.py`; `Clock`, `HistoricalClock` $\rightarrow$ `src/engine/backtest/clock.py`; `validate_utc_timestamp`, `create_utc_timestamp`, `BaseId` $\rightarrow$ `src/data/timeframe.py` & `src/data/dataset.py`; `StrategyId` $\rightarrow$ `src/strategies/signal.py`.
  * **Toàn bộ Unit Test Suite PASS 100%**: 115/115 unit tests vượt qua 100%.
  * **Golden Baseline Verification**: `run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` đạt **PASSED 100.0000% NUMERICAL MATCH**.

- Thực hiện thành công bài task Refactor Về Kiến Trúc Cuối Cùng (FINAL ARCHITECTURE) theo [REQ-20261002-refactor-final-architecture.md](file:///d:/reverse_indi/docs/requirements/REQ-20261002-refactor-final-architecture.md):
  * **Cấu trúc Thư mục Chuẩn Hóa**:
    - `src/config/`: Configuration layer.
    - `src/data/`: Single Source of Truth cho market data, data loading và dataset specifications.
    - `src/features/`: Indicators, zones, registry.
    - `src/strategies/`: Strategy contracts, DSL, context, reference strategies.
    - `src/trading/`:
      - `execution/`: Order, fill, broker, fill_model, slippage, fees, funding, execution engine.
      - `portfolio/`: Account, position, portfolio, pnl, margin, risk.
      - `backtest.py`: BacktestEngine, HistoricalClock, Clock, BacktestResult, EnvironmentFactory, run_trade_simulation.
    - `src/experiments/`: Planner, splitter, optimizer (Optuna Bayesian WFO), runner, window.
    - `src/evaluation/`: Metrics, alpha decay, reporting.
  * **Giải thể triệt để**: Xóa sạch toàn bộ các thư mục cũ `src/engine/`, `src/environment/`, và `src/market_data/`.
  * **Bảo vệ ranh giới kiến trúc (DAG Guard)**: `tests/architecture/test_dependency_direction.py` đạt **PASS 100%** (ngăn chặn triệt để mọi phụ thuộc ngược từ `strategies` vào `trading`).
  * **Toàn bộ Unit Test Suite PASS 100%**: Tất cả **115/115 unit tests** trong thư mục `tests/` chạy thành công **100% OK**.
  * **Golden Behavioral Baseline Verification**: `run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` đạt **PASSED 100.0000% NUMERICAL MATCH** (103/103 trades, Final Equity Exact Match = $11,812.54).
  * **Pipeline Benchmark Verification**: `run_pipeline.py --benchmark-trials 5` chạy mượt mà, hoàn thành trong 1.89s (377.4 ms/trial).

## What's next
- Khắc phục `AUDIT-RISK-01`: Cấu hình và tích hợp Stop-Distance Position Sizing ($Qty = \frac{Capital \times Risk\%}{|Entry - Stop|}$) và Margin Rejection vào `RiskManager`.
- Khắc phục `AUDIT-CFG-01` & `AUDIT-FUND-01`.

## Open issues / Notes
- Toàn bộ codebase hiện tuân thủ chặt chẽ kiến trúc 3-tier layering: `Research (Data, Features, Strategies)` -> `Trading Engine (Execution, Portfolio, Backtest)` -> `Evaluation (Metrics, Alpha Decay, Reporting)`.
- `AUDIT-RISK-01` (HIGH): `config/fixed_params.yaml` chứa `risk_per_trade_pct: 0.02` nhưng chưa được nạp vào `RiskManager` / `BacktestEngine` (đang dùng lot cố định 1.0).
