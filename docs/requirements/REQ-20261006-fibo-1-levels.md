# Requirement Specification (REQ)

- **ID**: REQ-20261006-fibo-1-levels
- **Title**: Add immutable custom Fibonacci level set fibo_1
- **Created Date**: 2026-10-06
- **Status**: Completed

## 1. Overview & Objective

Add one explicit, immutable custom Fibonacci level set named `fibo_1` under `src/features/fibo/`, containing exactly the 21 user-provided ratios in their supplied order.

## 2. Scope & Target Architectural Layer

Feature constants only. This task does not calculate swings, draw chart objects, alter zones, or change a strategy.

## 3. Detailed Approach & Steps

1. Create the `fibo` feature package and expose an immutable `FIBO_1_LEVELS` tuple.
2. Add a small read-only accessor for consumers.

## 4. Files TO Modify

- [x] `src/features/fibo/__init__.py`
- [x] `src/features/fibo/fibo_1.py`
- [x] `src/features/__init__.py`

## 5. Acceptance Criteria

- [x] `FIBO_1_LEVELS` contains exactly 21 specified values in order.
- [x] Consumers receive an immutable tuple.
- [x] No existing indicator, zone, or strategy behavior changes.

## 6. Verification Plan

- [x] Compile/import passed; user explicitly requested no test file.

## 7. Result

- Status: Completed. Import check passed and returned all 21 supplied levels in order.
