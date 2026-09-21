# Backtest Engine Subsystem (`src/backtest/`)

## 1. Overview & Purpose
`src/backtest/` is the **historical simulation orchestrator** of the Quant Lab platform.
It iterates historical market data observations chronologically, driving the end-to-end simulation pipeline:
```text
Market Observation
         │
         ▼
Advance Clock (HistoricalClock)
         │
         ▼
StrategyContext (Read-Only)
         │
         ▼
Strategy.on_bar(context) -> Signal
         │
         ▼
Signal -> Order Translation (Phase 1 Directional Intent)
         │
         ▼
ExecutionEngine.submit_order(order)
         │
         ▼
ExecutionEngine.process_market_data(tick) -> Fills
         │
         ▼
Portfolio.apply_fill(fill) & mark_to_market()
         │
         ▼
    BacktestResult (Immutable Read-Only Fact Payload)
```

The Backtest Engine enforces:
1. **Determinism**: Same Dataset + Config + Strategy + Seed = Identical `BacktestResult`.
2. **Zero Lookahead**: Historical clock advancement follows bar timestamps strictly.
3. **Subsystem Isolation**: Subsystem boundaries (`ExecutionEngine`, `Portfolio`, `Strategy`) are respected; `BacktestEngine` does not bypass execution or directly mutate portfolio accounts.

---

## 2. Key Architecture & Responsibilities

- **Warmup vs Execution Windows**: Supports `ExperimentRun.window` bounds (`warmup_start`, `execution_start`, `execution_end`). During warmup, strategy context and features are computed without generating trade orders.
- **Directional Signal Translation**: Translates `SignalAction` (`LONG`, `SHORT`, `HOLD`) vs active position into `Order` requests (`BUY`, `SELL`, or 2-step position reversal orders).
- **Fact-Only Output Container**: Returns an immutable `BacktestResult` capturing simulation facts without calculating performance metrics (metrics belong to `evaluation`).

---

## 3. Main Classes & Public API

### `BacktestEngine` (`src/backtest/engine.py`)
Orchestrator class:
- **Constructor**: `BacktestEngine(environment: Environment, strategy: Strategy, run: Optional[ExperimentRun] = None, default_order_quantity: float = 1.0)`
- **Methods**: `run(df: Optional[pd.DataFrame] = None) -> BacktestResult`

### `BacktestResult` (`src/backtest/result.py`)
Frozen dataclass capturing simulation facts:
- **Metadata**: `run_id`, `strategy_id`, `dataset_id`, `initial_capital`
- **Summary**: `bars_processed`, `final_timestamp`
- **Immutable Tuples**: `signals`, `orders`, `fills`, `portfolio_history`
- **Final Snapshot**: `final_portfolio`
- **Properties**: `final_cash`, `final_equity`, `realized_pnl`, `total_fees`

### `BacktestState` (`src/backtest/state.py`)
Internal mutable collector container populated during simulation loop execution.

### Exceptions (`src/backtest/exceptions.py`)
- `BacktestError` (inherits from `QuantSystemError`)
- `BacktestExecutionError`
- `InvalidSimulationStateError`

---

## 4. Dependencies
- Base: `src.core` (`QuantSystemError`, `validate_utc_timestamp`)
- Environment: `src.environment` (`Environment`)
- Strategy: `src.strategies` (`Strategy`, `StrategyContext`, `SignalAction`, `Signal`)
- Execution: `src.execution` (`Order`, `OrderSide`, `OrderType`, `Fill`, `ExecutionEngine`)
- Portfolio: `src.portfolio` (`Portfolio`, `Position`, `PositionSide`, `PortfolioState`)
- Experiments: `src.experiments` (`ExperimentRun`, `TimeWindow`)
