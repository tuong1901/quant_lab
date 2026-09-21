# Core Subsystem (`src/core/`)

Nền tảng primitive types, temporal UTC validation, entity ID system, clock abstraction (Historical & Realtime), base event model, và base exception của Quant Lab.

---

## Core Constitution (7 Luật Kiến Trúc)

1. **Core chỉ chứa Primitives**, không chứa Business Logic, Trading rules hay Strategy.
2. **Core tuyệt đối không import ngược Domain Subsystems** (`execution`, `portfolio`, `market_data`, `config`, `experiments`, `strategies`).
3. **Core không chứa khái niệm Sàn/Chiến lược** (Không Binance, BTCUSDT, Order, Position, Fill, Indicator, BacktestResult trong Core).
4. **Core hoàn toàn Deterministic**.
5. **Các đối tượng Core là bất biến (Immutable - `frozen=True`)**.
6. **Core chỉ phụ thuộc duy nhất vào Python stdlib** (`dataclasses`, `datetime`, `uuid`, `enum`, `typing`). Không phụ thuộc vào `pandas`, `numpy`, `yaml` hay bất kỳ thư viện thứ 3 nào.
7. **Quy tắc Nghi ngờ**: Khi không chắc một chức năng có thuộc Core hay không -> Giữ chức năng đó ở bên ngoài Core.

---

## Danh Sách Components (`src/core/`)

- **[exceptions.py](file:///d:/reverse_indi/src/core/exceptions.py)**: Ngoại lệ gốc `QuantSystemError(Exception)` cho toàn bộ Quant Lab framework.
- **[types.py](file:///d:/reverse_indi/src/core/types.py)**: `validate_utc_timestamp`, `create_utc_timestamp`, và primitive type aliases (`Symbol = str`, `Price = float`, `Quantity = float`).
- **[ids.py](file:///d:/reverse_indi/src/core/ids.py)**: Dataclasses ID bất biến (`BaseId`, `ExperimentId`, `RunId`, `StrategyId`, `OrderId`, `FillId`, `DatasetId`, `EventId`) hỗ trợ `generate()`.
- **[clock.py](file:///d:/reverse_indi/src/core/clock.py)**: `Clock` (Protocol), `HistoricalClock` (cho backtest simulation với `advance_to` không được lùi thời gian), và `RealtimeClock` (trả về UTC now).
- **[events.py](file:///d:/reverse_indi/src/core/events.py)**: Dataclass bất biến `Event` (`event_id`, `timestamp` UTC, `sequence`).
- **[__init__.py](file:///d:/reverse_indi/src/core/__init__.py)**: Export Public API.

---

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/core/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/core -v
```
- **15/15 Unit tests PASS 100%** (Thời gian chạy ~0.08s).
