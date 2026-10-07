# Requirement Specification (REQ)

- **ID**: REQ-20261007-continuous-reversal-pattern-criteria
- **Title**: Replace fixed reversal-pattern defaults with explicit continuous criteria
- **Created Date**: 2026-10-07
- **Status**: Completed

## 1. Overview & Objective

Remove hidden fixed thresholds from reversal-pattern detection. A caller must supply explicit real-valued criteria; pattern detection evaluates them only through inequality predicates such as `<=` and `>=`.

## 2. Scope & Target Architectural Layer

Candle feature API only. No search-space step/grid, config YAML, strategy, or trading change.

## 3. Detailed Approach & Steps

1. Introduce an immutable `ReversalPatternCriteria` value object with required threshold values.
2. Require it in `add_reversal_patterns` and retain the direct inequality rules.
3. Make the demo and tests pass a named criteria object explicitly.

## 4. Files TO Modify

- [x] `src/features/candle/pattern_reverse.py`
- [x] `src/features/candle/__init__.py`
- [x] `src/features/__init__.py`
- [x] `src/features/candle/demo.py`
- [x] `src/features/candle/visualize.py`
- [x] `tests/features/test_candle_reversal_patterns.py`

## 5. Acceptance Criteria

- [x] Detector has no implicit numerical thresholds.
- [x] Criteria accept continuous floats, not a discrete step grid.
- [x] Rules remain explicit `<=` / `>=` predicates and causal.

## 6. Verification Plan

- [x] Candle feature tests: 5 passed; visualizer PNG rendered.

## 7. Result

- Status: Completed. Runtime callers must supply continuous criteria explicitly; demo criteria remain demonstration-only.
