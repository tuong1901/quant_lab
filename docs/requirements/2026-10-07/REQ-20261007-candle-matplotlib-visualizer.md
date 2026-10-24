# Requirement Specification (REQ)

- **ID**: REQ-20261007-candle-matplotlib-visualizer
- **Title**: Add Matplotlib candle anatomy visualizer
- **Created Date**: 2026-10-07
- **Status**: Completed

## 1. Overview & Objective

Add a runnable Matplotlib demonstration that makes candle body, wicks, normalized geometry, and reversal-pattern evidence visually inspectable.

## 2. Scope & Target Architectural Layer

Hard-coded demo candles only. No TensorFlow, market-data CSV, production strategy, or backtest behavior is changed.

## 3. Detailed Approach & Steps

1. Reuse the candle demo frame and feature pipeline.
2. Draw OHLC candles with annotated anatomy and reversal-pattern labels.
3. Support showing the figure or saving it with an optional output path.

## 4. Files TO Modify

- [x] `src/features/candle/visualize.py`

## 5. Acceptance Criteria

- [x] Module renders a Matplotlib candlestick anatomy figure from demo data.
- [x] `--output <path>` saves a PNG without requiring an interactive display.

## 6. Verification Plan

- [x] Rendered and visually inspected `reports/candle_anatomy_demo.png`.

## 7. Result

- Status: Completed. Matplotlib was installed into the project venv and the PNG demo was rendered successfully.
