# Requirement Specification (REQ)

- **ID**: REQ-20261021-review-src-config
- **Title**: Review src/config correctness and runtime integration
- **Created Date**: 2026-10-21
- **Status**: Completed (source review only; no implementation authorized)

## 1. Overview & Objective
Review each src/config module and report concrete correctness issues with source evidence.

## 2. Scope & Target Architectural Layer
Config Python source, direct callers, domain types, and relevant test source. No production fixes.

## 3. Detailed Approach & Steps
1. Read project and config README/status; identify current entrypoint and dependencies.
2. Inspect validation, parsing, reference resolution, snapshots, and runtime parameter propagation.
3. Run only source-based checks without accessing data/config files; report findings and limits.

## 4. Files TO Modify
- This review REQ only. Implementation and other documentation edits require a separately approved scope.

## 5. Acceptance Criteria
- [x] Review all six Python modules in src/config.
- [x] Distinguish maintained runner defects from legacy defects.
- [x] Provide reproducible evidence and explain verification limits.

## 6. Verification Plan
- Source-only unit tests and in-memory probes with file I/O mocked where needed.
- Do not read YAML, market data, or fixture files without explicit permission.

## 7. Result
- Date: 2026-10-21. Source review completed; correctness issues found, no fixes applied.
- Maintained runner: atr_period is parsed but not forwarded by run_backtest.add_ema_features; numeric validation accepts NaN/infinity and risk_free_rate=-2 (rejected later by evaluation).
- Legacy loader: bool('false') enables allow_short; UTC parser retains non-UTC offsets; ExperimentTimeConfig accepts naive datetimes; snapshot calls absent Market.to_dict and omits resolved execution/portfolio/environment values.
- Existing model suite: 4/4 passed using python -B unittest discovery for test_models.py only.
- In-memory probes confirmed numeric/boolean/time issues and missing Market.to_dict. No YAML or market data was read or written.
- Existing validation-test setup uses StorageReference('local', 'dummy.parquet'), which raises InvalidDatasetError under the current type contract. Reference/reproducibility tests still depend on removed YAML files; full suite was not run.
- Real config/backtest.yaml contents and dataset descriptors are outside current read permission.
- Follow-up verification: exercised run_strict_backtest with file loaders, engine.run, and evaluation mocked; real constructors and feature assembly were retained. No data/config files accessed.
- Confirmed correct forwarding of capital, leverage, EMA periods, fixed quantity, seven risk/exit settings, and bps fee/slippage parameters. ATR period 7 was not forwarded: ATR received one positional argument and no keyword arguments.
- Runner omits context/clock initialization: synthetic ETH dataset metadata becomes default_dataset/BTCUSDT in the engine; clock defaults to 2020-01-01. These are runner/engine integration issues, not config parsing defects.
- Attribution correction: ATR propagation is a run_backtest.py defect. NaN/infinity acceptance is independently reproducible in src/config/runner.py. Legacy loader defects do not demonstrate failure of the maintained strict runner.
