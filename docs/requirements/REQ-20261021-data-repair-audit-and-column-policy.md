# Requirement Specification (REQ)

- **ID**: REQ-20261021-data-repair-audit-and-column-policy
- **Title**: Audit intentional candle repair and configure input columns explicitly
- **Created Date**: 2026-10-21
- **Status**: Completed (user approved implementation, descriptor edits and header-only CSV reads)

## 1. Overview & Objective
Preserve the user's explicitly confirmed open/high/low continuity repair. Report every repaired candle and require YAML-defined column handling rather than automatically exposing arbitrary input columns as features.

## 2. Scope & Target Architectural Layer
Dataset metadata, canonicalization, hashing, loader, compatibility adapter, their tests and documentation. Existing repair arithmetic stays unchanged. No automatic regeneration of production hashes or writes to market data.

## 3. Detailed Approach & Steps
1. Add WARNING diagnostics for each repaired candle: dataset identity when available, row position, timestamp, previous close, original and corrected open/high/low, reason. Report per-load totals at INFO. Direct canonicalization/hash calls and the legacy adapter must also emit repair warnings. Avoid duplicate repair events within one load/hash verification. Preserve the source frame and validate corrected output before returning it.
2. Add a typed column policy in Dataset YAML: explicit six-field source-to-canonical mapping, explicit ignored source names, declared numeric features with source name/type, and unknown-column rejection. Missing/ambiguous mappings, collisions, non-finite feature values and undeclared columns fail with named errors. Ignored columns are logged. No raw input columns enter MarketData unless mapped or declared as features.
3. Hash only validated pipeline inputs: preserve the current OHLCV hash representation when no features are declared; use a separately versioned deterministic representation including declared feature names/types/values when features are present. Verify before returning MarketData. Never update expected hashes automatically to hide a mismatch.
4. Require explicit policy for Dataset YAML; keep a documented canonical-only policy for direct Python callers, rejecting unknown fields rather than guessing aliases. The legacy CSV adapter must accept an explicit policy for noncanonical input and emit the same warnings. Normalize DataFrame row indexing for repair diagnostics without changing candle ordering.
5. Inspect ONLY headers of the three production derived CSVs after separate permission, then add exact mappings/ignore lists to their descriptors. Do not guess header case or extra fields. Production features stay empty unless the user identifies intended feature inputs.
6. Verify using synthetic in-memory frames, mocked file reads and captured logs. Update README/status to describe the intentionally retained repair behavior and eliminate the stale claim that high/low never change.

## 4. Files TO Modify
- [x] `src/data/columns.py` (new typed column policy and validation)
- [x] `src/data/dataset.py`
- [x] `src/data/versioning.py`
- [x] `src/data/loader.py`
- [x] `src/data/__init__.py`
- [x] `src/data/strict.py` (compatibility exports)
- [x] `tests/data/test_column_policy.py` (new)
- [x] `tests/data/test_repair_audit.py` (new)
- [x] `tests/data/test_critical_contracts.py`
- [x] `tests/data/test_versioning_hash.py` (verified unchanged; no edit needed)
- [x] `tests/mutation/test_data_contract_mutations.py`
- [x] `tests/e2e/test_strict_data_pipeline.py`
- [x] `tests/e2e/test_run_backtest_cli.py`
- [x] `config/datasets/testm15_strict_full.yaml`
- [x] `config/datasets/testm15_strict_1000.yaml`
- [x] `config/datasets/testm15_strict_100.yaml`
- [x] `src/data/README.md`
- [x] `PROJECT_STATUS.md`
- [x] This REQ

`config/backtest.yaml` is read-only context: it currently selects testm15_strict_full.yaml. Historical REQs are retained as history; the new confirmed policy supersedes the old high/low preservation requirement.

## 5. Acceptance Criteria
- [x] Every repaired candle emits a WARNING through all supported entrypoints, with before/after and reason; valid unchanged candles do not emit repair warnings.
- [x] Loader logs summary counts and rejection errors; no corrupted output bypasses validation.
- [x] YAML explicitly controls column mapping, ignores and numeric feature allowlist.
- [x] Unknown columns fail; dropped columns are reported; only canonical OHLCV plus declared features reach consumers.
- [x] Feature changes alter the feature-aware hash; OHLCV-only digest remains compatible when canonical values are unchanged.
- [x] Missing policies fail clearly; descriptor migration uses verified headers rather than assumptions.
- [x] Synthetic tests cover direct helpers, hash calls, legacy adapter, loader, duplicate indexes, schema errors, logs and hash compatibility.

## 6. Verification Plan
Run smallest relevant tests after each step. Convert touched fixture-dependent tests to mocked/in-memory I/O where practical. Do not run real-data E2E or read existing fixture contents without separate permission.

## 7. Data Access and Result
- Approved read already completed: config/backtest.yaml and the three config/datasets/testm15_strict_*.yaml descriptors.
- User approved implementation, descriptor edits and the three header-only reads. Read exactly one header line from data/derived/testm15_strict_full.csv, data/derived/testm15_strict_1000.csv and data/derived/testm15_strict_100.csv; no candle rows read or written.
- Verified headers match: time, open, high, low, close, five named Trend columns, Volume, Signal. All three descriptors now explicitly map time/Volume and ignore those five Trend columns plus Signal. No production input features enabled.
- Passed 2026-10-21: 44 targeted tests together (5 column policy, 7 repair audit, 16 critical data, 4 hash, 1 mutation covering six corruptions, 3 synthetic E2E, 8 runner integration). git diff --check passed.
- Critical/mutation/E2E tests now use mocked physical boundaries and synthetic frames. Rejection checks identify invariant errors rather than passing merely because fixture hashing failed.
- Feature type support is explicitly float64, finite and non-null. Source policies are immutable; unknown columns are rejected. The OHLCV-only serialization matches an independently constructed v1 digest.
- Production expected hashes remain unchanged. Real-data E2E/hash verification was not run. Storage timezone assumptions and DataRange edge coverage remain outside this change.
- Logging uses the application's standard logging configuration; normal CLI output reaches stderr and logs/backtest.log. Direct helper calls emit WARNING records without configuring application handlers.
