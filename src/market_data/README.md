# Market & Dataset Subsystem (`src/market_data/`)

Hệ thống quản lý dữ liệu thị trường (`Market & Dataset Subsystem`) độc lập, bất biến (immutable), deterministic và có khả năng reproduce 100% dữ liệu lịch sử làm nền tảng cho toàn bộ Quant Research System.

---

## Architecture Principles

1. **Phân Tách Bắt Buộc giữa Market và Dataset**:
   - `Market`: Định danh thị trường (`venue`, `symbol`, `market_type`, `quote_currency`). Không chứa `timeframe`, `data_range`, hay `OHLCV`.
   - `Dataset`: Bộ dữ liệu cụ thể (`dataset_id`, `market`, `timeframe`, `version`, `data_range`, `source`, `content_hash`, `storage_reference`).

2. **Tính Bất Biến (Immutability & Reproducibility)**:
   - `Dataset` là historical truth. Một khi đã đăng ký, các trường `version`, `data_range`, `content_hash`, `storage_reference` không bao giờ bị mutate.
   - Dataset Identity format: `dataset_id:v{version}` (ví dụ: `btcusdt_binance_perp_15m:v3`).

3. **Dataset Range khác Experiment Range**:
   - Dataset xác định dữ liệu hiện có từ đâu tới đâu. Experiment chỉ dùng một phần Dataset và tự quản lý `warmup` mà không làm thay đổi hay tạo mới Dataset.

4. **Xác Minh Content Hash & Validate OHLCV Strict**:
   - `content_hash` được tính toán deterministic bằng SHA-256 từ canonicalized DataFrame.
   - `DatasetLoader` validate chặt chẽ tính đơn điệu của timestamp (UTC), quan hệ OHLC (`high >= max(open, close)`, `low <= min(open, close)`, `volume >= 0`), và phát hiện nến thiếu (missing candles) mà không tự động forward-fill raw data.

5. **Phù Hợp Tương Thích Giữa Strategy Dataset & Execution Dataset**:
   - Cho phép Experiment reference `M15 strategy dataset` và `M1 execution dataset` đồng thời, kiểm tra tính tương thích (`venue`, `symbol`, `market_type`, `quote_currency`, `date_overlap`).

---

## Danh Sách Components (`src/market_data/`)

- **[exceptions.py](file:///d:/reverse_indi/src/market_data/exceptions.py)**: Ngoại lệ tùy chỉnh (`MarketDataException`, `InvalidMarketError`, `InvalidDatasetError`, `CatalogError`, `DatasetNotFoundError`, `DuplicateDatasetError`, `DataValidationError`, `IncompatibleDatasetError`).
- **[market.py](file:///d:/reverse_indi/src/market_data/market.py)**: Dataclass bất biến `Market` (`frozen=True`) mô tả danh tính thị trường.
- **[timeframe.py](file:///d:/reverse_indi/src/market_data/timeframe.py)**: Enum `Timeframe` (`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`) hỗ trợ serialization chuẩn dạng chuỗi (`"15m"`) và quy đổi phút/giây.
- **[dataset.py](file:///d:/reverse_indi/src/market_data/dataset.py)**: Dataclasses bất biến `DataRange`, `StorageReference`, `Dataset` (`identity -> dataset_id:v3`).
- **[versioning.py](file:///d:/reverse_indi/src/market_data/versioning.py)**: Engine tính toán SHA-256 content hash deterministic (`calculate_content_hash`, `verify_dataset_hash`).
- **[catalog.py](file:///d:/reverse_indi/src/market_data/catalog.py)**: Registry `DatasetCatalog` (`register`, `get`, `exists`, `list`, `list_versions`).
- **[loader.py](file:///d:/reverse_indi/src/market_data/loader.py)**: `DatasetLoader` và container `MarketData` (đọc Parquet/CSV, validate UTC timestamp, OHLC bounds, content hash, missing candles).
- **[compatibility.py](file:///d:/reverse_indi/src/market_data/compatibility.py)**: Hàm `validate_compatible_datasets(strategy_ds, execution_ds)`.
- **[__init__.py](file:///d:/reverse_indi/src/market_data/__init__.py)**: Export Public API.

---

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/market_data/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/market_data -v
```
- **29/29 Unit tests PASS 100%** (Thời gian chạy ~0.78s).
