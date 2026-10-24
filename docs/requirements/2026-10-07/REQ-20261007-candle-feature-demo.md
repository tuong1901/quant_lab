# Requirement Specification (REQ)

- **ID**: REQ-20261007-candle-feature-demo
- **Title**: Add runnable candle feature demonstration
- **Created Date**: 2026-10-07
- **Status**: Completed

## 1. Overview & Objective

Add a self-contained runnable script inside `src/features/candle/` that displays how example candles are decomposed into anatomy, normalized values, and reversal-pattern evidence.

## 2. Scope & Target Architectural Layer

Demo only. It uses hard-coded example OHLC candles; it does not read a CSV, change production features, or create orders.

## 3. Detailed Approach & Steps

1. Create example bullish, bearish, doji, pin-bar, and engulfing candles.
2. Run the existing feature functions and print selected input/output columns clearly.
3. Document the one-command invocation in the script docstring.

## 4. Files TO Modify

- [x] `src/features/candle/demo.py`

## 5. Acceptance Criteria

- [x] `python -m src.features.candle.demo` prints an understandable candle-component table.
- [x] The script has no external data dependency and does not mutate production configuration.

## 6. Verification Plan

- [x] Module run passed and printed all selected feature columns.

## 7. Result

- Status: Completed. Demo uses six hard-coded candles and no market-data file.
