# Requirement Specification (REQ)

- **ID**: REQ-20261006-continuity-wick-repair
- **Title**: Repair continuity-adjusted candle wick bounds by candle direction
- **Created Date**: 2026-10-06
- **Status**: Draft

---

## 1. Overview & Objective

When continuity cleaning replaces a discontinuous candle open with the preceding close, preserve that corrected open and repair only the invalid wick bound implied by candle direction. This replaces the previous open-clamp behavior that could lose continuity.

## 2. Scope & Target Architectural Layer

`src/data/versioning.py` canonical OHLCV cleaning and its strict-data tests. No original CSV is changed.

## 3. Detailed Approach & Steps

1. Detect discontinuous opens and set each corrected open to the preceding close.
2. For a green or flat candle (`close >= corrected_open`), set `low = corrected_open` only when existing low is above the corrected open.
3. For a red candle (`close < corrected_open`), set `high = corrected_open` only when existing high is below the corrected open.
4. Leave valid existing wicks unchanged; retain strict validation for all other OHLC breaches.
5. Replace the obsolete continuity-high-clamp test and add both green- and red-candle repair cases.

## 4. Files TO Modify

- [ ] `src/data/versioning.py`
- [ ] `tests/data/test_critical_contracts.py`
- [ ] `tests/mutation/test_data_contract_mutations.py` (only if its expected invalid case overlaps the new valid repair)
- [ ] `docs/requirements/REQ-20261006-continuity-wick-repair.md`
- [ ] `PROJECT_STATUS.md`

## 5. Acceptance Criteria

- [ ] A corrected green/flat candle has `low <= open <= high` and keeps `open == previous close`.
- [ ] A corrected red candle has `low <= open <= high` and keeps `open == previous close`.
- [ ] Existing valid high/low values are not changed.
- [ ] Original source CSV files are not modified.
- [ ] Strict data contract and mutation suites pass.

## 6. Verification Plan

- [ ] `python -m unittest tests.data.test_critical_contracts tests.mutation.test_data_contract_mutations`
- [ ] Re-check `data/testm15_indi.csv` read-only for strict-contract violations after canonicalization.

## 7. Result

- Status: Pending approval
- Date: N/A
