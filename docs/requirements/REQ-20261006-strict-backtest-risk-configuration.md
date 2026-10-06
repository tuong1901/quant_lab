# Requirement Specification (REQ)

- **ID**: REQ-20261006-strict-backtest-risk-configuration
- **Title**: Single YAML risk, sizing, execution, and exit configuration for strict backtest
- **Created Date**: 2026-10-06
- **Status**: In Progress

---

## 1. Overview & Objective

Make `config/backtest.yaml` the single configuration source for `python run_backtest.py`. It must control account capital/leverage, fixed or risk-based sizing, execution costs, and exit policy; current strict execution must no longer silently ignore those settings.

## 2. Scope & Target Architectural Layer

Strict production path only: `backtest.yaml -> typed runner config -> Portfolio/Execution/strategy exits -> BacktestResult`. Legacy WFO/research configuration remains untouched until it is separately migrated.

## 3. Detailed Approach & Steps

1. Extend typed YAML configuration and validation for account, risk, execution, and exit settings.
2. Inject configured capital/leverage, fee/slippage models, and risk limits into strict engine creation.
3. Add deterministic ATR or percentage stop-loss and fixed-RR take-profit handling; calculate size from current equity and stop distance when `sizing_mode: risk_per_trade`.
4. Preserve T+1 order timing, portfolio accounting, and closed-trade ledger evidence.
5. Add focused configuration, sizing, RR-exit, and strict runner tests; document the exact YAML contract.

## 4. Files TO Modify

- [x] `config/backtest.yaml`
- [x] `src/config/runner.py`
- [x] `src/trading/backtest.py`
- [ ] `src/trading/portfolio/risk.py`
- [ ] `src/trading/execution/`
- [x] `run_backtest.py`
- [ ] `tests/config/`
- [ ] `tests/trading/` or `tests/portfolio/`
- [ ] `tests/e2e/`
- [x] `src/config/README.md`
- [x] `PROJECT_STATUS.md`

## 5. Acceptance Criteria

- [ ] One edit to `config/backtest.yaml` changes the next strict run's capital, leverage, order sizing, fee/slippage, and risk settings.
- [ ] `risk_per_trade_pct` uses `equity * risk_pct / abs(entry - stop)` and rejects invalid/no-stop configurations.
- [ ] Stop-loss and fixed-RR take-profit orders respect causal T+1/intrabar execution contracts.
- [ ] Fixed-quantity mode remains available for reference experiments.
- [ ] Runner reports the active sizing/exit configuration and costs used.
- [ ] Legacy `portfolio.yaml`, `execution.yaml`, and `fixed_params.yaml` are not deleted or repurposed in this task.

## 6. Verification Plan

- [x] YAML parser check: loaded risk_per_trade=1%, ATR=14, RR=2.
- [ ] Deterministic sizing and RR lifecycle contract tests.
- [ ] Strict runner E2E using the approved test dataset descriptor.

## 7. Decisions Required

- Stop-loss source: ATR multiplier or fixed percentage.
- Take-profit: fixed RR or trailing stop only.
- On an opposite EMA signal while a position is open: immediately reverse at T+1 open, or keep the position until its stop/target exits.

## 8. Result

- Status: In progress. Defaults approved: ATR stop, fixed 2R target, immediate T+1 reversal, and stop-first handling when one OHLC candle touches both exits.
