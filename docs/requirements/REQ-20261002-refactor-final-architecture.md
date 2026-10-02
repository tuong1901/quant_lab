# Requirement Specification (REQ)

- **ID**: REQ-20261002-refactor-final-architecture
- **Title**: Refactor to Final Target Architecture (Consolidate to `src/trading/`, `src/data/`)
- **Created Date**: 2026-10-02
- **Status**: Proposed (Awaiting Explicit Approval)

---

## 1. Overview & Objective

Consolidate the codebase into the final locked architecture:
```text
src/
├── config/
├── data/
├── features/
├── strategies/
├── trading/
│   ├── execution/
│   │   ├── order.py
│   │   ├── fill.py
│   │   ├── broker.py
│   │   ├── fill_model.py
│   │   ├── slippage.py
│   │   ├── fees.py
│   │   └── funding.py
│   ├── portfolio/
│   │   ├── account.py
│   │   ├── position.py
│   │   ├── portfolio.py
│   │   ├── pnl.py
│   │   ├── margin.py
│   │   └── risk.py
│   └── backtest.py
├── experiments/
│   ├── planner.py
│   ├── splitter.py
│   └── optimizer.py
└── evaluation/
    ├── metrics.py
    ├── alpha_decay.py
    └── reporting.py
```

**PRIMARY CONTRACT**:
Zero behavior or semantic changes. 100% preservation of T+1 causal loop, execution rules, accounting rules, determinism, and 100.0000% numerical match against Golden Baseline.

---

## 2. Target Mapping & File Ownership

| Current File / Package | Final Location | Responsibility |
| :--- | :--- | :--- |
| `src/market_data/` | `src/data/` | Market data ingestion, validation, versioning, catalog, timeframe |
| `src/engine/execution/` | `src/trading/execution/` | Order, Fill, Broker, ExecutionEngine |
| `src/engine/models/` | `src/trading/execution/` | FillModel, Slippage, Fees (`fees.py`), Funding |
| `src/environment/accounting/` | `src/trading/portfolio/` | Account, Position, Portfolio, PnL, Margin, Risk (`risk.py`) |
| `src/engine/backtest/` & `src/environment/runtime/` | `src/trading/backtest.py` | Causal T+1 loop orchestrator (`BacktestEngine`), clock, state, result, simulator |
| `src/engine/backtest/optimizer.py` | `src/experiments/optimizer.py` | Optuna WFO bayesian study & plateau champion evaluator |
| `src/config/` | `src/config/` | Config loader, models, validation |
| `src/features/` | `src/features/` | Causal indicators, zones, registry |
| `src/strategies/` | `src/strategies/` | Strategy DSL contract, context, signal, reference strategies |
| `src/evaluation/` | `src/evaluation/` | Performance metrics, alpha decay, reporting |

---

## 3. Detailed Approach & Steps

1. **Move Data Subsystem**:
   - Rename/move `src/market_data/` to `src/data/`.
2. **Construct `src/trading/` Infrastructure**:
   - `src/trading/execution/`: Combine `order.py`, `fill.py`, `broker.py`, `fill_model.py`, `slippage.py`, `fees.py` (renamed from `fee.py`), `funding.py`, `execution_engine.py`, `exceptions.py`.
   - `src/trading/portfolio/`: Combine `account.py`, `position.py`, `portfolio.py`, `pnl.py`, `margin.py`, `risk.py` (renamed from `risk_manager.py`), `portfolio_state.py`, `exceptions.py`.
   - `src/trading/backtest.py`: Implement single coordinator with `BacktestEngine`, `HistoricalClock`, `Clock`, `BacktestState`, `BacktestResult`, `run_trade_simulation`.
3. **Move Optimizer to Experiments**:
   - Move `src/engine/backtest/optimizer.py` to `src/experiments/optimizer.py`.
4. **Remove Obsolete Folders**:
   - Remove `src/engine/` and `src/environment/`.
5. **Update Imports Across All Modules & Tests**:
   - Replace `src.market_data`, `src.engine`, `src.environment` imports with `src.trading`, `src.data`, `src.experiments`.
6. **Update Architecture Guard (`tests/architecture/test_dependency_direction.py`)**:
   - Protect final 3-tier layering: `Research` -> `Trading Engine` -> `Evaluation`.
   - Enforce: `strategies` never imports `execution` or `portfolio`.
7. **Verification**:
   - Run `.\venv\Scripts\python.exe -m unittest discover -s tests`.
   - Run `.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json`.
   - Run `.\venv\Scripts\python.exe run_pipeline.py --benchmark-trials 5`.
8. **Documentation**:
   - Update `README.md`, `src/README.md`, `PROJECT_STATUS.md`.

---

## 4. Files TO Modify / Move / Remove

- **New / Relocated**:
  - `src/data/*` (from `src/market_data/*`)
  - `src/trading/execution/*`
  - `src/trading/portfolio/*`
  - `src/trading/backtest.py`
  - `src/experiments/optimizer.py`
- **Removed**:
  - `src/market_data/`
  - `src/engine/`
  - `src/environment/`
- **Updated**:
  - `run_backtest.py`, `run_pipeline.py`
  - `tests/*`
  - `README.md`, `src/README.md`, `PROJECT_STATUS.md`

---

## 5. Acceptance Criteria

- [x] Folder structure exactly matches Section 1 of user specification.
- [x] No `src/engine/`, `src/environment/`, or `src/market_data/` directories remain.
- [x] Architecture guard enforces DAG strictly (no strategy -> trading leaks).
- [x] All unit tests pass 100%.
- [x] Golden baseline returns **PASSED 100.0000% NUMERICAL MATCH**.
- [x] `run_pipeline.py` executes without errors.

---

## 6. Verification Commands

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests
.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json
.\venv\Scripts\python.exe run_pipeline.py --benchmark-trials 5
```

---

## 7. Result
- Status: Approved & Completed
- Date: 2026-10-02
- Details:
  - Architecture Guard: `Ran 1 test in 0.134s OK` (0 DAG violations, `strategies` never imports `trading`).
  - Unit Tests: `Ran 115 tests in 0.743s OK` (100% pass rate).
  - Golden Baseline Verification: `PASSED 100.0000% NUMERICAL MATCH!` (Total Trades: 103, Final Equity Exact Match: $11812.54).
  - Benchmark Run: `run_pipeline.py --benchmark-trials 5` completed in 1.89 seconds (377.4 ms/trial).
