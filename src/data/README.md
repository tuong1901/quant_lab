# Tầng dữ liệu thị trường — src/data

Luồng production: Dataset YAML -> Dataset.from_yaml() -> DatasetLoader.load()
-> MarketData(dataset, df) -> features -> backtest.

## Trách nhiệm từng module

| Module | Trách nhiệm |
|---|---|
| columns.py | ColumnPolicy/FeatureColumn bất biến; mapping, ignore, feature allowlist và kiểm tra schema |
| dataset.py | Dataset, DataRange, StorageReference; parse/serialize YAML và column policy |
| market.py | Chuẩn hóa market identity: VENUE:SYMBOL:MARKET_TYPE:QUOTE_CURRENCY |
| timeframe.py | Timeframe và helper datetime UTC |
| versioning.py | Chọn cột, chuẩn hóa số/thời gian, sửa continuity có cảnh báo, kiểm tra OHLCV và hash |
| loader.py | Đọc CSV/Parquet, kiểm tra thời gian/range/cadence/hash, log kết quả hoặc lỗi |
| catalog.py | Registry theo dataset identity/version |
| compatibility.py | So market, timeframe và giao nhau của DataRange |
| exceptions.py | Ngoại lệ dùng chung cho data |
| strict.py, __init__.py | Export API; strict.py chỉ là lớp tương thích import |

Các module trong src/data chỉ phụ thuộc trực tiếp vào nội bộ data và thư viện ngoài.
Không phụ thuộc trực tiếp vào config, features, strategies hoặc trading.

## Chính sách cột bắt buộc trong Dataset YAML

Ví dụ đúng với header ba derived CSV đã được phép kiểm tra:

```yaml
columns:
  mapping:
    timestamp: time
    open: open
    high: high
    low: low
    close: close
    volume: Volume
  ignore: ["Trend Chính 1", "Trend Chính 2", "Trend Chính 3", "Trend Phụ 1", "Trend Phụ 2", "Signal"]
  features: {}
  unknown: reject
```

- Mapping là **tên canonical -> tên cột nguồn**, phân biệt chữ hoa/thường.
- YAML phải khai báo đủ mapping, ignore, features, unknown. Thiếu policy sẽ báo lỗi.
- Thiếu cột bắt buộc, cột nguồn trùng, mapping xung đột hoặc cột chưa khai báo đều bị từ chối.
- Cột ignore có mặt sẽ được bỏ và ghi INFO; tên ignore vắng mặt không gây lỗi.
- Output chỉ chứa sáu cột canonical theo thứ tự cố định và feature đã khai báo.
- Không tự dò time/date/Volume hay tự đưa các cột còn lại vào feature.
- Chính sách Python mặc định ColumnPolicy() chỉ nhận sáu tên canonical, không có cột thừa.
  Caller dùng alias phải truyền policy rõ ràng.

Muốn nhận một feature từ storage, khai báo source và type:

```yaml
  features:
    score:
      source: RawScore
      type: float64
```

Hiện hỗ trợ float64 hữu hạn, không null. Sai kiểu hoặc NaN/infinity bị từ chối.
Tên feature không được trùng tên OHLCV/timestamp. Một cột nguồn chỉ có một vai trò.
Ba descriptor production hiện có features rỗng; Trend/Signal không được đưa vào engine.

## Sửa continuity có chủ ý và có cảnh báo

Đây là quy tắc được người dùng xác nhận lại ngày 2026-10-21:

1. Giữ nguyên nến đầu tiên và nến đã có open bằng close trước.
2. Với nến gián đoạn, đặt open bằng close nến trước.
3. Nếu open mới làm vượt range: hạ low cho nến xanh/flat hoặc nâng high cho nến đỏ
   theo điều kiện hiện có; không clamp open về high.
4. Kiểm tra OHLCV sau sửa; lỗi không được quy tắc xử lý vẫn bị từ chối.
5. Không ghi đè nguồn, không sắp xếp lại nến. Reset row index để index trùng không nhân bản dòng.

Mỗi nến bị sửa phát một WARNING gồm dataset, vị trí dòng (bắt đầu từ 0), timestamp,
close nến trước, open/high/low trước và sau, cùng reason=open_close_discontinuity.
INFO tổng hợp số dòng, số nến sửa và số sửa từng trường. Gọi trực tiếp hàm repair,
canonicalization, hash hoặc adapter cũ cũng phát cảnh báo khi sửa.

DatasetLoader không chuẩn hóa lần hai khi kiểm tra hash, nên một lần load không
ghi lặp cảnh báo cho cùng nến. Nếu dữ liệu bị từ chối sau sửa, log lỗi nêu rõ;
cảnh báo sửa không có nghĩa dataset đã qua kiểm định.

Dùng CLI hiện tại để ghi stderr và logs/backtest.log:
```powershell
.\venv\Scripts\python.exe run_backtest.py
.\venv\Scripts\python.exe run_backtest.py --log-level DEBUG
```
Module data sử dụng logging chuẩn, không tự thay cấu hình handler của ứng dụng.

## Hash và đường gọi

calculate_content_hash(raw, columns=dataset.columns, dataset_identity=dataset.identity)
nhận **dữ liệu nguồn cùng policy tương ứng**. Không đưa frame đã đổi tên về canonical
vào lại một policy vẫn trỏ tới time/Volume.

- Không có feature: giữ nguyên chuỗi byte OHLCV v1, nên digest không đổi nếu các
  giá trị canonical không đổi. Chưa tính lại hoặc tự cập nhật hash production.
- Có feature: dùng schema hash ohlcv-features-v2, chứa sáu trường canonical cùng
  tên/type/value của feature theo thứ tự tên xác định. Thay feature làm đổi hash.
- Cột ignore không ảnh hưởng hash vì không được chuyển cho pipeline.
- Thêm feature vào descriptor yêu cầu xác lập digest tương ứng trên nguồn đã kiểm chứng.
  Loader không tự sửa expected hash để cho dữ liệu qua.

load_m15_ohlcv(path, columns=...) là adapter deprecated: cùng policy/repair/cadence,
có cảnh báo thiếu kiểm chứng descriptor/hash. Production dùng DatasetLoader.

## Ràng buộc thời gian hiện có và giới hạn

DataRange metadata từ chối datetime không timezone và chuẩn hóa về UTC; range là
[start, end). Loader từ chối timestamp trùng/đảo thứ tự, nằm ngoài range, gap hoặc
cadence không đều. Nó không lấp gap.

Chính sách parse timestamp storage hiện vẫn dùng pandas utc=True: timestamp nguồn
không timezone được hiểu là UTC. Loader chưa bắt buộc phủ đủ đầu/cuối DataRange
hoặc khớp mốc đồng hồ của sàn. Các vấn đề này chưa được đổi trong REQ hiện tại.
MarketData là frozen container nhưng DataFrame bên trong vẫn có thể thay đổi;
consumer chịu trách nhiệm không làm sai dữ liệu đã kiểm chứng.

## Kiểm chứng

Tests mới dùng dữ liệu giả trong bộ nhớ, mock file boundary và capture log.
Các test critical/mutation/E2E liên quan đã bỏ việc đọc/ghi fixture vật lý.
Chúng kiểm tra policy, cảnh báo qua các entrypoint, repair high/low, index trùng,
hash v1/feature-aware, schema rejection và luồng thực tới engine/evaluation.

Tham chiếu: docs/requirements/REQ-20261021-data-repair-audit-and-column-policy.md.
Các REQ cũ mô tả giữ nguyên high/low là lịch sử và được quy tắc xác nhận ở trên thay thế.
