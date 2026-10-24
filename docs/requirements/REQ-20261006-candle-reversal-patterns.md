# Requirement Specification (REQ)

- **ID**: REQ-20261006-candle-reversal-patterns
- **Title**: Add candle reversal-pattern features
- **Created Date**: 2026-10-06
- **Status**: Completed

## 1. Overview & Objective

Add causal candle reversal-pattern features under `src/features/candle/pattern_reverse.py`. They describe candlestick evidence only; they never submit orders or decide a trade.

## 2. Scope & Target Architectural Layer

Use only existing anatomy/normalization columns plus the immediately prior candle where required. No trend filter, zones, Fibonacci, strategy, or trading changes.

## 3. Detailed Approach & Steps

1. Add rule-based boolean features for bullish/bearish pin bars and bullish/bearish engulfing candles.
2. Make thresholds explicit function arguments with conservative defaults: small body <= 30% range, dominant rejection wick >= 50% range, close position >= 70% or <= 30%.
3. Require a prior candle only for engulfing; the first row must safely evaluate false.
4. Add focused rules/causality/no-mutation tests and export the feature function.

## 4. Files TO Modify

- [x] `src/features/candle/pattern_reverse.py`
- [x] `src/features/candle/__init__.py`
- [x] `src/features/__init__.py`
- [x] `tests/features/test_candle_reversal_patterns.py`

## 5. Acceptance Criteria

- [x] Output contains four causal boolean columns for bullish/bearish pin and engulfing patterns.
- [x] Pattern code consumes candle primitives and does not recalculate OHLC anatomy.
- [x] No output leads directly to BUY/SELL.
- [x] First candle cannot be engulfing and input frame remains unchanged.

## 6. Verification Plan

- [x] Focused candle primitives + reversal-pattern tests: 5 passed.

## 7. Result

- Status: Completed. Four reversal-pattern features were added with no strategy/trading integration.
