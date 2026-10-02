# Requirement Specification (REQ)

- **ID**: REQ-20261002-dissolve-core-folder
- **Title**: Dissolve `src/core/` and Redistribute Entities to Domain Owners
- **Created Date**: 2026-10-02
- **Status**: Completed

---

## 1. Overview & Objective

The `src/core/` folder currently houses generic entities (`types.py`, `clock.py`, `ids.py`, `events.py`, `exceptions.py`). Having a generic `core` folder creates confusion about entity ownership and introduces unnecessary abstraction layers.

**OBJECTIVE**:
Dissolve `src/core/` completely. Move all primitives, clocks, IDs, and exceptions into their direct Domain Owners (`src/data/`, `src/environment/accounting/`, `src/engine/execution/`, `src/engine/backtest/`, `src/strategies/`, `src/experiments/`), while maintaining **100% test pass rate (115/115 tests)** and **100.0000% Golden Baseline numerical match**.

---

## 2. Target Mapping & Domain Ownership

| Current Entity in `src/core/` | Target Location (Domain Owner) |
| :--- | :--- |
| `PositionSide` | `src/environment/accounting/position.py` |
| `OrderSide`, `Price`, `Quantity`, `Symbol`, `OrderId`, `FillId` | `src/engine/execution/order.py` & `src/engine/execution/fill.py` |
| `Clock`, `HistoricalClock`, `RealtimeClock` | `src/engine/backtest/clock.py` |
| `validate_utc_timestamp`, `create_utc_timestamp` | `src/data/timeframe.py` |
| `DatasetId` | `src/data/dataset.py` |
| `StrategyId` | `src/strategies/strategy.py` |
| `ExperimentId`, `RunId` | `src/experiments/run.py` |
| `Event`, `EventId` | `src/engine/execution/order.py` |
| `QuantSystemError` | `src/data/exceptions.py` (root exception) |

---

## 3. Detailed Approach & Steps

1. Relocate symbols from `src/core/` to their target files as mapped above.
2. Remove `src/core/` directory and all files inside it.
3. Update imports across `src/` and `tests/`.
4. Run `.\venv\Scripts\python.exe -m unittest discover -s tests`.
5. Run `.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json`.
6. Update `README.md`, `src/README.md`, and `PROJECT_STATUS.md`.

---

## 4. Files TO Modify / Remove

- [x] Remove: `src/core/types.py`, `src/core/clock.py`, `src/core/ids.py`, `src/core/events.py`, `src/core/exceptions.py`, `src/core/__init__.py`
- [x] Modify: Target domain modules in `src/data/`, `src/environment/`, `src/engine/`, `src/strategies/`, `src/experiments/`, `src/config/`, and tests.

---

## 5. Acceptance Criteria

- [x] Thư mục `src/core/` bị xóa 100%.
- [x] Tất cả các entity được sở hữu bởi đúng Domain tương ứng.
- [x] All 115 unit tests pass 100%.
- [x] Golden baseline returns **PASSED 100.0000% NUMERICAL MATCH**.

---

## 6. Verification Commands

```bash
.\venv\Scripts\python.exe -m unittest discover -s tests
.\venv\Scripts\python.exe run_backtest.py --verify-golden-baseline tests/fixtures/golden_baseline_v1.json
```

---

## 7. Result
- Status: Completed
- Date: 2026-10-02
- Verification: 115/115 unit tests passed, Golden baseline 100.0000% numerical match.
