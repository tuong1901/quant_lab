# Requirement Specification (REQ)

- **ID**: REQ-20261006-remove-recapitalization
- **Title**: Remove recapitalization and external-capital accounting
- **Created Date**: 2026-10-06
- **Status**: Completed

## 1. Overview & Objective

Remove the recently added automatic capital injection mechanism and every associated recapitalization/cash-flow accounting path. Restore one initial-capital account backtest behavior.

## 2. Scope & Target Architectural Layer

Portfolio accounting, backtest result metadata, evaluation presentation, runner output, generated recap report, and recapitalization requirement documents only.

## 3. Detailed Approach & Steps

1. Remove Account external-capital state and injection method.
2. Remove Portfolio recap trigger, events, cycle UID, and recap module.
3. Remove recap metadata from BacktestResult and restore initial-capital evaluation formulas.
4. Remove recap report generation/presentation from runner and delete generated recap report.
5. Verify compilation and strict runner's normal no-recap behavior.

## 4. Files TO Modify

- [x] `src/trading/portfolio/account.py`
- [x] `src/trading/portfolio/portfolio.py`
- [x] `src/trading/portfolio/__init__.py`
- [x] `src/trading/portfolio/recapitalization.py` (deleted)
- [x] `src/trading/backtest.py`
- [x] `src/evaluation/metrics.py`
- [x] `run_backtest.py`
- [x] `reports/recapitalization_report.json` (deleted)
- [x] `docs/requirements/REQ-20261006-account-recapitalization.md` (deleted)
- [x] `docs/requirements/REQ-20261006-remove-recapitalization.md`

## 5. Acceptance Criteria

- [x] No source imports or invokes recapitalization/injection code.
- [x] No external-capital fields remain in account/result/evaluation output.
- [x] Backtest uses only its original initial capital and preserves original negative-balance exception behavior.

## 6. Result

- Status: Passed (source scan and Python compilation)
