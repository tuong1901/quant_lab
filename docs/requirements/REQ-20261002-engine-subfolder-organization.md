# Requirement Specification (REQ)

- **ID**: REQ-20261002-engine-subfolder-organization
- **Title**: Subdivide Domain Folders (Engine & Environment) into Granular Sub-packages
- **Created Date**: 2026-10-02
- **Status**: Completed

---

## 1. Overview & Objective

Repository `src/` currently has consolidated physical domain folders (`engine`, `environment`, `data`, `features`, `strategies`, `evaluation`). However, directories like `src/engine/` (16 flat files) and `src/environment/` (14 flat files) contain many modules under a single directory level.

**OBJECTIVE**:
Subdivide `src/engine/` and `src/environment/` into intuitive, single-responsibility sub-packages (`execution`, `models`, `backtest`, `accounting`, `runtime`), while maintaining **100% backward-compatible re-exports** via `__init__.py` to guarantee zero broken imports and **100.0000% exact numerical match**.

---

## 2. Technical Design & Subpackage Structure

### A. Sub-packaging `src/engine/`

```
src/engine/
├── exceptions.py
├── __init__.py                 # SSOT re-exporting all engine public symbols
├── execution/                  # Execution Engine & Order/Fill Entities
│   ├── order.py
│   ├── fill.py
│   ├── result.py
│   ├── broker.py
│   └── execution_engine.py
├── models/                     # Fill, Slippage, Fee, Funding Models
│   ├── fill_model.py
│   ├── slippage.py
│   ├── fee.py
│   └── funding.py
└── backtest/                   # Backtest Loop, Orchestration & Optimization
    ├── state.py
    ├── backtest_result.py
    ├── backtest_engine.py
    ├── simulator.py
    └── optimizer.py
```

### B. Sub-packaging `src/environment/`

```
src/environment/
├── exceptions.py
├── __init__.py                 # SSOT re-exporting all environment public symbols
├── accounting/                 # Accounting, Portfolio, Margin & Risk Management
│   ├── account.py
│   ├── position.py
│   ├── pnl.py
│   ├── margin.py
│   ├── risk_manager.py
│   ├── portfolio_state.py
│   └── portfolio.py
└── runtime/                    # Runtime Composition, Factory & Context
    ├── context.py
    ├── environment.py
    ├── factory.py
    └── registry.py
```

---

## 3. Strict Acceptance Criteria

1. [x] **Subpackage Consolidation**: Files in `src/engine/` and `src/environment/` are logically grouped into `execution/`, `models/`, `backtest/`, `accounting/`, `runtime/`.
2. [x] **Backward Compatibility**: `src/engine/__init__.py` and `src/environment/__init__.py` re-export all symbols so zero external code breaks.
3. [x] **Architecture & Test Integrity**:
   - `tests/architecture/test_dependency_direction.py` passes 100%.
   - All 115 unit tests pass 100%.
4. [x] **100.0000% Golden Baseline Match**: `run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json` returns **PASSED 100.0000% NUMERICAL MATCH**.

---

## 4. Verification Commands

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests
.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json
```

---

## 5. Result
- Status: Completed
- Date: 2026-10-02
- Verification: 115/115 unit tests passed. Golden baseline verified with 100.0000% exact numerical match (103 trades, $11,812.54 final equity).
