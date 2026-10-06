# Requirement Specification (REQ)

- **ID**: REQ-20261006-terminal-liquidation-cutoff
- **Title**: Limit terminal summary to the initial account liquidation boundary
- **Created Date**: 2026-10-06
- **Status**: Draft

## 1. Overview & Objective

Keep the full recapitalized simulation and audit history, but make terminal output report only the initial account through the first time mark-to-market equity reaches zero or below. All later cycles and final recapitalized outcome are exported to a report file only.

## 2. Scope & Target Architectural Layer

Output/evaluation projection only. Recapitalization trigger remains `equity <= 500`; this requirement uses the independent terminal cutoff `equity <= 0`.

## 3. Detailed Approach & Steps

1. Record the first zero-or-below-equity timestamp and initial-cycle terminal snapshot before recapitalization obscures it.
2. Render terminal summary only from initial capital through that liquidation boundary; if no liquidation occurs, render the ordinary initial-cycle final summary.
3. Export full JSON/Markdown report containing all funding cycles, recap events, post-liquidation timeline, total external capital, and final cash-flow-aware result.
4. Add tests for zero-equity cutoff, continued simulation after cutoff, and report-only post-cutoff visibility.

## 4. Files TO Modify

- [ ] `src/trading/portfolio/portfolio.py`
- [ ] `src/trading/backtest.py`
- [ ] `src/evaluation/metrics.py`
- [ ] `src/evaluation/reporting.py`
- [ ] `run_backtest.py`
- [ ] `tests/e2e/test_terminal_liquidation_cutoff.py` (new)
- [ ] `README.md`
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261006-terminal-liquidation-cutoff.md`

## 5. Acceptance Criteria

- [ ] Terminal summary ends at first `equity <= 0` for the initial account.
- [ ] Recapitalization and simulation continue after that timestamp.
- [ ] Full report contains post-cutoff cycles/events/final result.
- [ ] No terminal metric includes post-cutoff recapitalized capital.

## 6. Result

- Status: Pending approval
