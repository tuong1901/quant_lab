# Requirement Specification (REQ)

- **ID**: REQ-20261005-data-contract-strict-pipeline
- **Title**: Chốt Data Contract và đưa strict data pipeline vào đường production
- **Created Date**: 2026-10-05
- **Status**: Completed

---

## 1. Overview & Objective
Thiết lập một data contract duy nhất cho dữ liệu OHLCV: thời gian UTC, khoảng dữ liệu, định danh market, hash canonical và gap policy. Loại bỏ đường nạp CSV lỏng khỏi runner production để mọi backtest đi qua `Dataset -> DatasetLoader -> MarketData`. Thay các test API cũ bằng critical contract, mutation, integration và E2E tests.

## 2. Scope & Target Architectural Layer
Tầng `src/data` là SSOT cho data contract. Runners, config dataset metadata và E2E test chỉ được thay đổi để tiêu thụ strict pipeline này; không thay đổi logic feature, strategy hay execution ngoài wiring cần thiết.

## 3. Detailed Approach & Steps
1. Chốt contract trong code và README: timestamp luôn UTC-aware/canonical UTC; `DataRange` là `[start, end)`; market identity gồm venue, symbol, market type và quote currency đã chuẩn hoá; hash dùng schema/cột/thứ tự/dtype/value canonical; gap không được tự fill và phải fail strict load.
2. Hoàn thiện các value object, catalog, hash, loader và compatibility theo contract; giữ `load_m15_ohlcv` chỉ như adapter deprecated nội bộ hoặc xoá khi runners đã chuyển đổi được.
3. Thêm metadata YAML cho dataset production và đổi `run_backtest.py`/`run_pipeline.py` sang `DatasetCatalog` + `DatasetLoader`, không đọc CSV trực tiếp.
4. Viết 10–15 critical contract tests, mutation tests cho timestamp/OHLC/hash/schema/gap/range, một integration YAML → Dataset → Loader → MarketData, sau đó cập nhật unit tests theo API mới.
5. Thêm E2E Dataset → Feature → Strategy → Backtest, dùng slice 20–100 candles từ dữ liệu thật được cấp quyền; chạy các test nhỏ nhất sau từng bước.

## 4. Files TO Modify
- [ ] `src/data/__init__.py`
- [ ] `src/data/market.py`
- [ ] `src/data/timeframe.py`
- [ ] `src/data/dataset.py`
- [ ] `src/data/versioning.py`
- [ ] `src/data/catalog.py`
- [ ] `src/data/loader.py`
- [ ] `src/data/compatibility.py`
- [ ] `src/data/README.md`
- [ ] `run_backtest.py`
- [ ] `run_pipeline.py`
- [ ] `config/datasets.yaml` (hoặc một dataset YAML mới, nếu cấu trúc hiện hữu yêu cầu)
- [ ] `tests/data/test_market.py`
- [ ] `tests/data/test_dataset.py`
- [ ] `tests/data/test_loader_validation.py`
- [ ] `tests/data/test_versioning_hash.py`
- [ ] `tests/data/test_catalog.py`
- [ ] `tests/data/test_compatibility.py`
- [ ] `tests/data/test_integration.py`
- [ ] `tests/data/test_critical_contracts.py` (new)
- [ ] `tests/mutation/test_redteam_mutations.py`
- [ ] `tests/e2e/test_strict_data_pipeline.py` (new)
- [ ] `PROJECT_STATUS.md`

## 5. Acceptance Criteria
- [ ] UTC, `[start, end)`, full market identity, canonical SHA-256 hash và strict gap policy được mô tả và kiểm tra bằng code.
- [ ] Không còn runner production nào gọi `load_m15_ohlcv`; runner nạp dữ liệu qua Dataset metadata và `DatasetLoader`.
- [ ] Có 10–15 critical contract tests tập trung vào behavior/risk, không kiểm tra getter đơn thuần.
- [ ] Mutation tests chứng minh loader từ chối các dạng dữ liệu bị phá hỏng trọng yếu.
- [ ] Integration YAML → Dataset → Loader → MarketData pass.
- [ ] E2E strict pipeline từ Dataset đến Backtest pass trên 20–100 candles từ `D:\reverse_indi\data\valm15-indivip_signal.csv`.
- [ ] Test data subsystem liên quan pass; tài liệu/status phản ánh behavior mới.

## 6. Verification Plan
- [ ] Chạy targeted `tests/data` sau từng logical step.
- [ ] Chạy mutation tests liên quan.
- [ ] Chạy E2E strict-pipeline test với slice dữ liệu thật đã được phê duyệt.
- [ ] Chạy architecture/dependency check và test runner CLI phù hợp nếu không cần chạy full benchmark.

## 7. Result
- Status: In progress — strict core, compatibility, critical tests, and real-data E2E implemented.
- Date: 2026-10-05
- Verification: `python -m unittest tests.data.test_critical_contracts tests.e2e.test_strict_data_pipeline` passed (13 tests) with elevated test-fixture write permission.
- Real-data E2E: passed with a read-only 64-candle slice from `data/valm15-indivip_signal.csv`.
- Mutation verification: `python -m unittest tests.mutation.test_data_contract_mutations` passed; it corrupts schema, finite values, OHLC, volume and candle cadence.
- CLI verification: `run_pipeline.py --help` and `run_backtest.py --help` both expose `--dataset-definition`; production paths load `Dataset.from_yaml()` through `DatasetLoader`.
- Data access requested: Đọc duy nhất `D:\reverse_indi\data\valm15-indivip_signal.csv`, chỉ lấy 20–100 candles để xác minh E2E và không sửa file. Cần quyền riêng để đọc `C:\Users\tuong.hc\.codex\attachments\75e752b2-1688-45a8-82a3-863d6e2b020e\pasted-text.txt` nếu nội dung của nó là contract/test-case đầu vào cần áp dụng.
