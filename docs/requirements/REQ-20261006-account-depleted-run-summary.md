# Requirement Specification (REQ)

- **ID**: REQ-20261006-account-depleted-run-summary
- **Title**: Add execution timeline to the account-depleted terminal report
- **Created Date**: 2026-10-06
- **Status**: Draft

## 1. Overview & Objective

When a backtest account is depleted, print a compact run summary rather than only an accounting error: dataset/strategy, first and last processed timestamp, processed bar count, signal/order/fill counts, final order/fill timestamp, and depletion accounting cause.

## 2. Scope & Target Architectural Layer

Backtest partial-run capture and terminal formatting only. No trading, data, or accounting policy changes.

## 3. Files TO Modify

- [ ] `src/trading/backtest.py`
- [ ] `run_backtest.py`
- [ ] `tests/e2e/test_account_depleted_summary.py` (new)
- [ ] `docs/requirements/REQ-20261006-account-depleted-run-summary.md`

## 4. Acceptance Criteria

- [ ] Depletion log prints run start/end, bars processed, signals/orders/fills, and last order/fill time when present.
- [ ] Existing accounting reason remains factual and present.
- [ ] Successful backtest output is unchanged.

## 5. Result

- Status: Pending approval
