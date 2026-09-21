# Strategy Subsystem (`src/strategies/`)

## 1. Overview & Purpose
`src/strategies/` defines the **Phase 1 Strategy Contract** boundary for the Quant Lab platform.
A Strategy is strictly responsible for:
- Reading a narrow, read-only `StrategyContext` (timestamp, price, current position side, feature map).
- Evaluating directional intent and returning a value object `Signal` (`SignalAction.HOLD`, `SignalAction.LONG`, or `SignalAction.SHORT`).

A Strategy is **NOT** responsible for:
- Creating or executing orders.
- Interacting with `Broker` or `ExecutionEngine`.
- Modifying `Portfolio` or calculating account PnL/margin/fees/slippage.
- Loading data or parsing `yaml` config files directly.
- Running backtest loops or evaluating performance metrics.

---

## 2. Key Architecture & Boundaries

```text
Market / Features / Position (Read-Only)
                 │
                 ▼
          StrategyContext
                 │
                 ▼
             Strategy (Protocol)
                 │
                 ▼
               Signal (HOLD / LONG / SHORT)
                 │
                 ▼
          Backtest Engine (Phase 2)
```

1. **Directional Intent**: `SignalAction` values represent desired target directional state (`LONG`, `SHORT`, `HOLD`). Position state transitions and order executions are managed by downstream execution & portfolio engines.
2. **Stateless Evaluation**: `strategy.on_bar(context)` takes a read-only frozen context and returns a frozen `Signal` payload without side effects or external mutations.
3. **No External Dependencies**: The `Strategy` layer depends only on primitive types from `core` and `portfolio`. It MUST NOT depend on `backtest`, `execution`, `broker`, `evaluation`, `generator`, `evolution`, or `paper`.

---

## 3. Main Classes & Public API

### `SignalAction` (`src/strategies/signal.py`)
Enum representing directional strategy intent: `HOLD`, `LONG`, `SHORT`.

### `Signal` (`src/strategies/signal.py`)
Frozen dataclass value object:
- **Attributes**: `timestamp`, `action`, `strategy_id`, `metadata`.

### `StrategyContext` (`src/strategies/context.py`)
Narrow read-only container passed to strategies:
- **Attributes**: `timestamp`, `price`, `position_side`, `features`.

### `Strategy` (`src/strategies/strategy.py`)
Protocol contract (`@runtime_checkable`):
- **Properties**: `strategy_id`
- **Methods**: `on_bar(context: StrategyContext) -> Signal`

### `EMAStrategy` (`src/strategies/ema.py`)
Reference strategy implementation:
- **Logic**: Evaluates fast/slow EMA features (`EMA20 > EMA50 -> LONG`, `EMA20 < EMA50 -> SHORT`, equal/missing -> `HOLD`).

### Exceptions (`src/strategies/exceptions.py`)
- `StrategyError` (inherits from `QuantSystemError`)
- `InvalidSignalError`
- `StrategyContextError`

---

## 4. Dependencies
- Base: `src.core` (`QuantSystemError`, `StrategyId`, `validate_utc_timestamp`)
- Portfolio: `src.portfolio.position` (`PositionSide`)
