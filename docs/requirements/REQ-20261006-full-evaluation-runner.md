# Requirement Specification (REQ)

- **ID**: REQ-20261006-full-evaluation-runner
- **Title**: Run complete designed evaluation from the backtest entrypoint
- **Created Date**: 2026-10-06
- **Status**: In Progress

## 1. Overview & Objective

Make `python run_backtest.py` execute and render the complete existing evaluation contract: strict accounting/risk plus Walk-Forward OOS evaluation, dual-fill comparison, alpha-decay, verdict, and persisted JSON/Markdown/CSV reports.

## 2. Scope & Target Architectural Layer

Unify the two runner entrypoints at the orchestration layer only; evaluation formulas remain owned by `src/evaluation/`. Runtime settings remain YAML-only.

## 3. Detailed Approach & Steps

1. Create a contiguous real-data derived input of at least 1,000 M15 candles from `testm15_indi.csv`; leave source data unchanged.
2. Extend runner YAML with WFO, benchmark, report, and full-evaluation settings.
3. Extract the existing WFO/evaluation orchestration from `run_pipeline.py` into a reusable function.
4. Call it from `run_backtest.py` after strict loading and render every existing report metric, verdict reason, alpha-decay horizon, and artifact path.
5. Keep accounting/risk summary visibly separate from WFO/OOS evaluation so their different execution models are not conflated.
6. Add an integration test proving YAML -> Loader -> WFO evaluation -> exported report artifacts.

## 4. Files TO Modify

- [ ] `data/derived/testm15_strict_full.csv` (new; 19,978 contiguous real candles)
- [ ] `config/datasets/testm15_strict_full.yaml` (new)
- [ ] `config/backtest.yaml`
- [ ] `config/pipeline.yaml`
- [ ] `src/config/runner.py`
- [ ] `run_backtest.py`
- [ ] `run_pipeline.py`
- [ ] `tests/e2e/test_full_evaluation_runner.py` (new)
- [ ] `README.md`
- [ ] `PROJECT_STATUS.md`
- [ ] `docs/requirements/REQ-20261006-full-evaluation-runner.md`

## 5. Acceptance Criteria

- [ ] `python run_backtest.py` requires no runtime flags.
- [ ] Output includes accounting/risk and all existing WFO report metrics.
- [ ] Output includes verdict, reasons, fill survival, alpha-decay, and report artifact paths.
- [ ] WFO settings and dataset path are editable only in YAML.
- [ ] Original CSV remains unchanged.

## 6. Verification Plan

- [ ] `python -m unittest tests.e2e.test_full_evaluation_runner`
- [ ] `python run_backtest.py`

## 7. Result

- Status: Pending approval
