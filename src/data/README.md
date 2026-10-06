# Phân Hệ Dữ Liệu Thị Trường (`src/data/`) — Source Catalog & Architecture Guide

Tài liệu này là Catalog & Hướng dẫn Kiến trúc toàn diện cho Phân hệ Dữ liệu Thị trường (`src/data/`), mô tả chi tiết chức năng, ý nghĩa, quan hệ liên kết và tác động hệ thống của từng file nguồn.

---

## 📑 Danh Mục File & Cấu Trúc Phân Hệ (`src/data/`)

```text
src/data/
├── __init__.py          # Export master SSOT public symbols cho data access
├── market.py            # Value Object Market (venue, symbol, quote_currency, market_type)
├── timeframe.py         # Enum Timeframe (M1..D1) & utility quy đổi giây/phút
├── dataset.py           # Entities DataRange, StorageReference & Dataset (YAML serialization)
├── versioning.py        # SHA-256 Content Hash Engine kiểm soát phiên bản dữ liệu
├── catalog.py           # Registry DatasetCatalog quản lý danh mục Dataset
├── loader.py            # DatasetLoader (Read CSV/Parquet, validate UTC, OHLC bounds, missing gaps) & load_m15_ohlcv()
├── compatibility.py     # Check tính tương thích dữ liệu giữa Strategy và Execution
└── exceptions.py        # Cây ngoại lệ tùy chỉnh cho phân hệ data
```

---

## 💡 Chi Tiết Từng Module

### 1. 📄 [src/data/market.py](file:///d:/reverse_indi/src/data/market.py)
- **[PURPOSE]**: Dataclass bất biến (`frozen=True`) đại diện cho thị trường giao dịch (`Market`).
- **[PROPERTIES / METHODS]**:
  - `identity`: Trả về canonical string e.g. `'BINANCE:BTCUSDT'`.
- **[SIDE EFFECTS & DEPENDENCIES]**: Ném `InvalidMarketError` nếu `venue`, `symbol` hoặc `quote_currency` bị rỗng.

### 2. 📄 [src/data/timeframe.py](file:///d:/reverse_indi/src/data/timeframe.py)
- **[PURPOSE]**: Enum `Timeframe` chuẩn hóa các khung thời gian nến (`M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`).
- **[METHODS]**:
  - `to_seconds() -> int`: Quy đổi khung thời gian ra giây.
  - `to_minutes() -> int`: Quy đổi khung thời gian ra phút.
  - `from_string(val: str) -> Timeframe`: Parse chuỗi e.g. `'15m'`, `'1h'` thành Enum `Timeframe`.

### 3. 📄 [src/data/dataset.py](file:///d:/reverse_indi/src/data/dataset.py)
- **[PURPOSE]**: Dataclass bất biến định nghĩa metadata cho một dataset (`DataRange`, `StorageReference`, `Dataset`).
- **[METHODS]**:
  - `Dataset.from_yaml(yaml_path) -> Dataset`: Parse cấu hình metadata dataset từ file YAML.
  - `identity`: Trả về canonical dataset identity string e.g. `'btcusdt_binance_perp_15m:v1'`.

### 4. 📄 [src/data/versioning.py](file:///d:/reverse_indi/src/data/versioning.py)
- **[PURPOSE]**: Tính toán mã hash SHA-256 nội dung của DataFrame (`calculate_content_hash(df)`).
- **[SIDE EFFECTS]**: Ném `DataValidationError` nếu DataFrame rỗng. Duyệt qua các cột `timestamp`, `open`, `high`, `low`, `close`, `volume` để mã hóa byte-stream deterministic.

### 5. 📄 [src/data/catalog.py](file:///d:/reverse_indi/src/data/catalog.py)
- **[PURPOSE]**: Registry `DatasetCatalog` quản lý và tra cứu các định nghĩa `Dataset`.
- **[METHODS]**:
  - `register(dataset)`: Đăng ký một `Dataset` vào memory catalog. Ném `DuplicateDatasetError` nếu trùng identity.
  - `get(identity)`: Tìm kiếm dataset theo identity hoặc `dataset_id`.
  - `load_from_file(yaml_path)` / `load_from_dir(dir_path)`: Đọc và đăng ký các file cấu hình YAML.

### 6. 📄 [src/data/loader.py](file:///d:/reverse_indi/src/data/loader.py)
- **[PURPOSE]**: `DatasetLoader` đọc file vật lý (CSV/Parquet) và thực hiện kiểm định tính toàn vẹn (Validation Pipeline).
- **[VALIDATION PIPELINE]**:
  1. Kiểm tra sự tồn tại của file vật lý.
  2. Parse CSV/Parquet sang DataFrame.
  3. Validate bắt buộc các cột `open`, `high`, `low`, `close`, `volume` và `timestamp`.
  4. Quy đổi và kiểm tra UTC timestamp: không được chứa `NaT`, không được trùng lặp (duplicate), phải tăng nghiêm ngặt (monotonic increasing), nằm trong khoảng `[data_range.start, data_range.end]`.
  5. Validate bất đẳng thức OHLC: `high >= low`, `high >= max(open, close)`, `low <= min(open, close)`, `volume >= 0`.
  6. Verify SHA-256 content hash so với `dataset.content_hash`.
  7. Phát hiện số nến bị thiếu (`detect_missing_candles`).
- **[HELPER FUNCTION]**: `load_m15_ohlcv(csv_path)` - Loader nhanh phục vụ CLI script runner.

### 7. 📄 [src/data/compatibility.py](file:///d:/reverse_indi/src/data/compatibility.py)
- **[PURPOSE]**: Hàm `validate_compatible_datasets(strategy_ds, execution_ds)` kiểm tra tính tương thích về Market và Timeframe giữa dữ liệu tạo chiến lược và dữ liệu thực thi.

---

## 🔗 DAG Dependency Position

## Strict Data Contract

- Timestamps are canonical UTC; naive timestamps are rejected.
- `DataRange` uses `[start, end)`: the start is included and the end is excluded.
- Market identity is `VENUE:SYMBOL:MARKET_TYPE:QUOTE_CURRENCY`.
- Dataset SHA-256 hashes canonical ordered `timestamp, open, high, low, close, volume` values.
- Before hashing and validation, only a candle whose `open` differs from the previous `close` is aligned; if that candidate open exceeds the candle's existing `high`, its open is clamped to that high. The source file remains unchanged.
- The loader rejects missing/irregular candles; it never fills gaps.
- Production runners require `--dataset-definition <descriptor.yaml>` and load it through `Dataset.from_yaml()` plus `DatasetLoader`.

```text
src.core -> src.config -> src.data
```
Phân hệ `src.data` chỉ được phép phụ thuộc vào `src.core` và `src.config`. Không phụ thuộc ngược vào `features`, `strategies`, `engine`, `environment` hay `evaluation`.
