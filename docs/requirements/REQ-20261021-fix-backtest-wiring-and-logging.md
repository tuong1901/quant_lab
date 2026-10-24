[text](../../run_backtest.py)# Requirement Specification (REQ)

- **ID**: REQ-20261021-fix-backtest-wiring-and-logging
- **Title**: Correct strict backtest configuration wiring and add function-level logs
- **Created Date**: 2026-10-21
- **Status**: Completed (approved by user: "Lam di")

## 1. Overview & Objective
Correct the confirmed strict-runner integration defects and expose the configuration actually consumed by each stage. User requested fixes and logs showing what is loaded when backtest.py is called.

## 2. Scope & Target Architectural Layer
Maintained strict runner and its configuration/engine integration. Legacy ConfigLoader and legacy simulation paths remain outside this change.
Function-level logging covers strict runner/config functions and BacktestEngine initialization/run/helpers, not every function across all project modules.

## 3. Detailed Approach & Steps
1. Validate finite numeric configuration values and risk_free_rate > -1 before dataset loading; preserve existing supported sizing modes and positive leverage semantics. Verify with isolated configuration tests.
2. Pass configured ATR period through feature construction. Initialize HistoricalClock from the first selected candle and ExecutionContext from the loaded dataset. Give the engine an explicit market symbol separate from run identity, preserving compatibility for existing callers. Reject an empty selected frame clearly. Verify non-BTC identity and pre-2020 clock behavior with synthetic in-memory inputs.
3. Add standard logging with time, level, module/function, input summary, completion, and error context. INFO logs show resolved configuration, dataset identity/path, row count/time range, EMA/ATR settings, portfolio/fee/slippage/risk settings, engine initialization, and final counts. DEBUG logs trace helper calls and per-bar operations. Do not dump complete candles/DataFrames or raw YAML.
4. CLI defaults to INFO on stderr and appends logs to logs/backtest.log; an optional log-level switch enables DEBUG function tracing. Logging is initialized only by the CLI, not at import. Tests capture logs in memory without writing runtime log files. Verify tracing and unchanged stdout report behavior.
5. Update documentation and status with verified behavior and remaining limitations.

## 4. Files TO Modify
- [x] `run_backtest.py`
- [x] `src/config/runner.py`
- [x] `src/trading/backtest.py`
- [x] `tests/config/test_runner_config.py` (new source-only tests)
- [x] `tests/engine/test_strict_runner_wiring.py` (new source-only tests)
- [x] `src/config/README.md`
- [x] `README.md`
- [x] `PROJECT_STATUS.md`
- [x] This REQ
- Runtime output after approval: `logs/backtest.log` (append only, generated when CLI is run).

## 5. Acceptance Criteria
- [x] Changing ATR period changes the period actually supplied to the indicator.
- [x] Dataset identity and order symbol reflect the loaded dataset; clock is initialized from selected data.
- [x] Invalid/non-finite numeric settings fail before market data loading.
- [x] Valid capital, leverage, sizing, fees, slippage, and exit parameters continue to reach their consumers correctly.
- [x] Each function in the stated strict-path scope has appropriate tracing; INFO reports loaded settings and DEBUG exposes helper/per-bar detail.
- [x] Logs include failures and never dump entire market datasets.
- [x] Focused synthetic tests pass; no real YAML/market data is accessed without separate permission.

## 6. Verification Plan
- After each logical step run its focused unittest checks, using mocked file boundaries and in-memory synthetic frames.
- Check ATR argument propagation, non-BTC symbols, dataset identity, pre-2020 clock, empty input, finite validation, log contents/levels, and constructor compatibility.
- Inspect available dependent test source before selecting any additional tests; skip suites reading protected fixtures/data.

## 7. Result
- Passed on 2026-10-21: 3 config tests and 8 real-engine synthetic integration/logging tests. git diff --check passed (only standard LF/CRLF notices).
- Numeric validation applies to direct dataclass construction as well as YAML parsing. Tests cover NaN/infinities, booleans, strings, overflow, zero costs, supported fractional leverage and invalid annual rates.
- Engine tests cover pre-2020 ETH candles, separate run/symbol identities, ATR period propagation and differing output, empty input, old caller compatibility, all runtime parameter forwarding, logs at INFO/DEBUG, and CLI stdout/failure handling.
- Output file setup was verified with mocked handlers; no runtime log file was created during testing. Actual append output is generated on CLI execution.
- Remaining limitations: real-data E2E not run; retired config API/tests and pre-existing ATR initialization/fill-bar timing are outside this repair.
- Proposed runtime log output: append `logs/backtest.log` for execution diagnostics; approval includes creating this output when the CLI runs. No existing log contents need to be read.
- No permission requested to read existing YAML, CSV, JSON, or other data files. Real-data E2E remains outside this implementation verification.
