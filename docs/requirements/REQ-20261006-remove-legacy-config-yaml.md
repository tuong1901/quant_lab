# Requirement Specification (REQ)

- **ID**: REQ-20261006-remove-legacy-config-yaml
- **Title**: Remove retired legacy YAML configuration path
- **Created Date**: 2026-10-06
- **Status**: Approved

## 1. Overview & Objective

Retire the unused WFO/pipeline YAML configuration path and retain only the strict `python run_backtest.py` configuration contract.

## 2. Scope & Target Architectural Layer

Delete exactly the ten user-approved legacy YAML files. Remove or update code/tests/docs that claim those files are runnable. Preserve `config/backtest.yaml` and every descriptor under `config/datasets/`.

## 3. Detailed Approach & Steps

1. Delete the approved YAML files only.
2. Remove legacy config-loader tests and stale documentation references.
3. Verify strict runner configuration still loads and record the result.

## 4. Files TO Modify

- [x] `config/default.yaml`
- [x] `config/datasets.yaml`
- [x] `config/execution.yaml`
- [x] `config/experiments.yaml`
- [x] `config/fixed_params.yaml`
- [x] `config/pipeline.yaml`
- [x] `config/portfolio.yaml`
- [x] `config/search.yaml`
- [x] `config/search_space.yaml`
- [x] `config/zones.yaml`
- [x] `tests/config/test_loader.py`
- [ ] `src/config/README.md`
- [ ] `README.md`
- [ ] `PROJECT_STATUS.md`

## 5. Acceptance Criteria

- [ ] The exact ten legacy YAML files are absent.
- [ ] `config/backtest.yaml` and strict dataset descriptors remain.
- [ ] `load_backtest_runner_config()` still loads the strict runner configuration.
- [ ] No maintained test/doc claims the deleted config path is runnable.

## 6. Verification Plan

- [ ] Confirm exact paths before deletion.
- [ ] Run strict YAML parser check.

## 7. Result

- Status: In progress; user explicitly approved deletion of the listed files.
