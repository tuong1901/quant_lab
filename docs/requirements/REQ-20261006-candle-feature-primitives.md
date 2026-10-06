# Requirement Specification (REQ)

- **ID**: REQ-20261006-candle-feature-primitives
- **Title**: Add causal candle anatomy and normalized geometry primitives
- **Created Date**: 2026-10-06
- **Status**: Completed

## 1. Overview & Objective

Create only the `src/features/candle/` primitive layer: immutable-by-copy OHLC anatomy, direction, intra-candle ratios, and optional normalization against a caller-provided causal ATR column.

## 2. Scope & Target Architectural Layer

No pattern recognition, swing/structure work, zones, Fibonacci, strategy signals, or trading behavior changes.

## 3. Detailed Approach & Steps

1. Add raw candle geometry and direction columns from valid OHLC.
2. Add range-relative ratios and optional ATR-relative ratios; zero range/invalid ATR produce NaN rather than fabricated values.
3. Add focused P0 tests for bullish/bearish/doji/zero-range, invariants, preservation, normalization, and causal-prefix safety.

## 4. Files TO Modify

- [x] `src/features/candle/__init__.py`
- [x] `src/features/candle/anatomy.py`
- [x] `src/features/candle/normalization.py`
- [x] `src/features/__init__.py`
- [x] `tests/features/test_candle_primitives.py`

## 5. Acceptance Criteria

- [x] Raw geometry preserves OHLC and satisfies body + wicks = range.
- [x] Direction is +1/0/-1 and body return is defined without divide-by-zero.
- [x] Zero-range and invalid ATR normalization values are NaN.
- [x] Feature functions are causal and do not mutate input frames.

## 6. Verification Plan

- [x] Focused candle primitive tests: 3 passed.

## 7. Result

- Status: Completed. Candle-only scope delivered; no patterns, structure, zones, Fibonacci, or strategy behavior was changed.
