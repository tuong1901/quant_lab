# Requirement Specification (REQ)

- **ID**: REQ-20261002-update-readme-architecture
- **Title**: Update Repository & Source Catalog Documentation (README.md & src/README.md)
- **Created Date**: 2026-10-02
- **Status**: Completed

---

## 1. Overview & Objective
Update root `README.md` and `src/README.md` to accurately reflect the finalized 6-domain consolidated architecture and the sub-package structure (`src/engine/` -> `execution/`, `models/`, `backtest/`; `src/environment/` -> `accounting/`, `runtime/`).
Ensure every directory and module includes:
- Purpose & Functionality
- Meaning & Role in Quant System
- File Links & Relationships
- Impact / Side Effects

---

## 2. Scope & Target Architectural Layer
- Layer: Documentation / Catalog
- Affected files:
  - `README.md`
  - `src/README.md`

---

## 3. Detailed Approach & Steps
1. Update `README.md` Section 3 (10-Phase Architecture & Directory Map) to reflect current 6 physical domain folders (`data`, `environment`, `features`, `strategies`, `engine`, `evaluation`) plus `core`, `config`, `experiments`, highlighting subpackage layouts.
2. Update `src/README.md` Catalog:
   - Synchronize folder tree to match actual physical filesystem.
   - Update `src/engine/` section detailing subpackages: `execution/`, `models/`, `backtest/`.
   - Update `src/environment/` section detailing subpackages: `accounting/`, `runtime/`.
   - Update `src/data/`, `src/features/`, `src/strategies/`, `src/evaluation/`, `src/config/`, `src/core/`, `src/experiments/` with exact files, inputs, outputs, file links, and system impact.
   - Refresh DAG Dependency Table & Verification section.

---

## 4. Files TO Modify
- [x] `README.md`
- [x] `src/README.md`

---

## 5. Acceptance Criteria
- [x] Folder maps match `src/` layout 100%.
- [x] Subpackages for `engine` and `environment` are fully documented with file links, functions, inputs, outputs, and impacts.
- [x] All markdown links point to existing files using standard file link markdown syntax.

---

## 6. Verification Plan
- Inspect generated markdown files for syntax correctness and broken links.
- Verify file references match current workspace.

---

## 7. Result
- Status: Completed
- Date: 2026-10-02
- Verification: 115/115 unit tests pass, Golden Baseline verification 100.0000% numerical match.
