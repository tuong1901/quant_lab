# Environment Subsystem (`src/environment/`)

## 1. Overview & Purpose
`src/environment/` is the **runtime composition layer** of the Quant Lab research system. It constructs and owns the runtime world containing all subsystem dependencies required for backtesting and experiment execution:
- **`Clock`**: Simulation time provider (`src.core.clock`).
- **`MarketData`**: Data loader and dataset slices (`src.market_data.loader`).
- **`Execution`**: Order execution engine (`src.execution.execution_engine`).
- **`Portfolio`**: Position and account accounting subsystem (`src.portfolio.portfolio`).
- **`Config`**: Typed experiment configuration model (`src.config.models`).
- **`Registry`**: Isolated dynamic dependency lookup container.

The Environment subsystem enforces **composition and dependency ownership** without housing domain business logic (e.g. trading decisions, PnL math, or strategy evaluations).

---

## 2. Key Architecture & Constraints

```text
                        CORE / CONFIG
                             │
     ┌───────────────────────┼───────────────────────┐
     │                       │                       │
MARKET_DATA              EXECUTION               PORTFOLIO
     │                       │                       │
     └───────────────────────┼───────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │ src/environment/    │
                  │                     │
                  │  Environment        │
                  │  ExecutionContext   │
                  │  Registry           │
                  │  EnvironmentFactory │
                  └─────────────────────┘
```

1. **Layer Rules**: `src/environment/` depends on lower-level core/config/market_data/execution/portfolio modules. It MUST NOT import higher-level domain modules (`strategies`, `backtest`, `evaluation`, `generator`, `evolution`, etc.).
2. **No Direct YAML Parsing**: Configuration is accepted strictly via typed `ExperimentConfig` objects provided by `src/config/`.
3. **No Global Singletons**: Every `Environment` instance owns its local `Registry` object. Shared global singletons are strictly prohibited to maintain full batch/parallel experiment safety.

---

## 3. Main Classes & Public API

### `Environment` (`src/environment/environment.py`)
Frozen dataclass representing the complete runtime container.
- **Attributes**: `clock`, `market_data`, `execution`, `portfolio`, `config`, `registry`.
- **Validation**: Enforces non-null checks on all attributes in `__post_init__`, raising `MissingDependencyError` if any dependency is omitted.

### `ExecutionContext` (`src/environment/context.py`)
Lightweight frozen dataclass encapsulating execution metadata during active strategy runs.
- **Attributes**: `clock`, `run`, `dataset_id`, `execution_id`.

### `Registry` (`src/environment/registry.py`)
Isolated key-value container for dynamic or optional services.
- **Methods**: `register(key, val)`, `get(key, default=None)`, `contains(key)`, `require(key)`.

### `EnvironmentFactory` (`src/environment/factory.py`)
Stateless assembly engine.
- **Method**: `EnvironmentFactory.create(config, clock=None, market_data=None, execution_engine=None, portfolio=None) -> Environment`.

### Exceptions (`src/environment/exceptions.py`)
- `EnvironmentError` (inherits from `QuantSystemError`)
- `EnvironmentConstructionError`
- `MissingDependencyError`
- `EnvironmentValidationError`

---

## 4. Dependencies
- Base: `src.core` (`QuantSystemError`, `Clock`, `HistoricalClock`, `RunId`)
- Config: `src.config` (`ExperimentConfig`, `ConfigLoader`)
- Market Data: `src.market_data` (`DatasetLoader`)
- Execution: `src.execution` (`ExecutionEngine`)
- Portfolio: `src.portfolio` (`Portfolio`)
