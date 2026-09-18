# Execution Subsystem (`src/execution/`)

Subsystem thực thi giao dịch độc lập, chịu trách nhiệm xử lý chuyển đổi từ **`Order` → `ExecutionEngine` → `FillModel` → `Fill` → `Portfolio`**.

---

## Architecture Principles

1. **Phân Tách Trách Nhiệm Tuyệt Đối (SRP)**:
   - Execution chỉ tập trung duy nhất vào đoạn `Order → Fill`.
   - Không chứa logic chiến lược (RSI, EMA, Trend), không quản lý tài khoản/accounting (Cash, Equity, Margin), không tính PnL và không đánh giá Sharpe/MaxDD.

2. **Khả Năng Thay Thế Dynamic FillModel**:
   - `FillModel` là một interface trừu tượng (`FillModel`). Có thể chuyển đổi linh hoạt giữa `OHLCFillModel`, `LowerTimeframeReplayFillModel`, `TickReplayFillModel`, hoặc `LiveBroker` mà **tuyệt đối không phải sửa đổi Strategy, Portfolio, hay Backtest Engine**.

3. **Lower-Timeframe Replay Loại Bỏ Lookahead**:
   - Khi backtest trên dữ liệu nến lớn (như Strategy M15), `LowerTimeframeReplayFillModel` duyệt chuỗi nến nhỏ (như M1) theo thứ tự thời gian thực tế để phân định chính xác mốc nến nào chạm TP hay SL trước mà **không tự đoán hay làm rò rỉ dữ liệu nến M1 ngược lại Strategy/Features**.

4. **100% Determinism & Audit Trail**:
   - Mọi Order fill tạo ra `ExecutionResult` tổng hợp và danh sách `ExecutionEvent` (OrderSubmitted, OrderAccepted, FillCreated, OrderFilled, v.v.) hỗ trợ audit vết giao dịch 100%.

---

## Danh Sách Components (`src/execution/`)

- **[exceptions.py](file:///d:/reverse_indi/src/execution/exceptions.py)**: Định nghĩa `ExecutionException`, `InvalidOrderError`, `FillModelError`, `SlippageError`, `FeeError`.
- **[order.py](file:///d:/reverse_indi/src/execution/order.py)**: Enums `OrderSide`, `OrderType`, `OrderStatus` và dataclass bất biến `Order` (`frozen=True`).
- **[fill.py](file:///d:/reverse_indi/src/execution/fill.py)**: Dataclass bất biến `Fill` (`frozen=True`) đại diện cho 1 lệnh đã khớp.
- **[result.py](file:///d:/reverse_indi/src/execution/result.py)**: Container `ExecutionResult` tổng hợp danh sách Fills, trung bình giá khớp, tổng phí và tổng trượt giá.
- **[fill_model.py](file:///d:/reverse_indi/src/execution/fill_model.py)**: Interface `FillModel`, `OHLCFillModel` (Single bar fill) và `LowerTimeframeReplayFillModel` (Intrabar M1 replay).
- **[slippage.py](file:///d:/reverse_indi/src/execution/slippage.py)**: `FixedSlippageModel` (Basis points / fixed ticks) và `VolatilitySlippageModel` (phụ thuộc ATR).
- **[fee.py](file:///d:/reverse_indi/src/execution/fee.py)**: `PercentageFeeModel` tính hoa hồng (Maker/Taker basis points).
- **[funding.py](file:///d:/reverse_indi/src/execution/funding.py)**: `PerpetualFundingModel` tính phí Funding Rate 8h cho Crypto Perpetuals.
- **[broker.py](file:///d:/reverse_indi/src/execution/broker.py)**: Gateway interface `Broker` và wrapper `HistoricalBroker`.
- **[execution_engine.py](file:///d:/reverse_indi/src/execution/execution_engine.py)**: Orchestrator quản lý lifecycle của Order và bắn `ExecutionEvent` audit log.
- **[__init__.py](file:///d:/reverse_indi/src/execution/__init__.py)**: Public API export.

---

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/execution/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/execution -v
```
- **12/12 Unit tests PASS 100%** (Thời gian chạy ~0.001s).
