# Requirement Specification (REQ)

- **ID**: REQ-20261006-test-suite-redundancy-cleanup
- **Title**: Remove proven redundant tests from the test suite
- **Created Date**: 2026-10-06
- **Status**: Draft

---

## 1. Overview & Objective

Remove only tests which either assert nothing or duplicate existing, more focused contract tests. Keep legacy compatibility, integration, mutation, and production-path coverage intact.

## 2. Scope & Target Architectural Layer

Test-suite maintenance only. No production-source or data changes.

## 3. Detailed Approach & Steps

1. Remove the no-op certification gate, whose sole test body is `pass`.
2. Remove the aggregate core smoke test; its UTC, clock, ID, and event assertions are each covered in `tests/core/`.
3. Remove the aggregate direct data-validator smoke test; strict data contract and mutation tests cover its rejection behaviour through the public loader.
4. Run the retained focused suites to prove the removed checks remain covered.

## 4. Files TO Modify

- [ ] `tests/certification/__init__.py` (delete with now-empty no-op package)
- [ ] `tests/certification/test_certification_gate.py` (delete)
- [ ] `tests/unit/test_unit_core.py` (delete)
- [ ] `tests/unit/test_unit_market_data.py` (delete)
- [ ] `PROJECT_STATUS.md` (record cleanup result)
- [ ] `docs/requirements/REQ-20261006-test-suite-redundancy-cleanup.md` (complete acceptance/result)

## 5. Acceptance Criteria

- [ ] No deleted test contains a unique assertion not preserved by a retained test.
- [ ] No-op certification test/package is absent.
- [ ] Core UTC/clock/ID/event tests still pass from `tests/core/`.
- [ ] Strict data contract and data mutation tests still pass.
- [ ] No source or data file changes are made.

## 6. Verification Plan

- [ ] `python -m unittest discover -s tests/core`
- [ ] `python -m unittest tests.data.test_critical_contracts tests.mutation.test_data_contract_mutations`
- [ ] `python -m unittest discover -s tests/unit`

## 7. Result

- Status: Pending approval
- Date: N/A
