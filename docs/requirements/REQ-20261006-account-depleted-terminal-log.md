# Requirement Specification (REQ)

- **ID**: REQ-20261006-account-depleted-terminal-log
- **Title**: Print a clear terminal log when the account is depleted
- **Created Date**: 2026-10-06
- **Status**: Completed

## 1. Overview & Objective

Replace the technical uncaught portfolio traceback with a clear terminal message when the backtest cannot continue because account balance is negative. The log explains the accounting cause from realized PnL, fees, funding, and the negative balance rather than asserting an unsupported cause.

## 2. Files TO Modify

- [x] `run_backtest.py`
- [x] `docs/requirements/REQ-20261006-account-depleted-terminal-log.md`

## 3. Acceptance Criteria

- [x] Negative-balance portfolio failure prints `ACCOUNT DEPLETED`, negative balance, realized PnL, fees, funding, and a factual reason derived from those values.
- [x] Successful runs retain their existing output and zero exit code.

## 4. Result

- Status: Passed
