# Portfolio & Accounting Subsystem (`src/portfolio/`)

Subsystem quản lý danh mục và tài khoản độc lập, chịu trách nhiệm hạch toán chính xác trạng thái tài khoản, vị thế, PnL, đòn bẩy và rủi ro sau khi nhận `Fill` từ `ExecutionEngine`.

---

## Architecture Principles

1. **Phân Tách Trách Nhiệm Tuyệt Đối (SRP)**:
   - `Portfolio` chỉ trả lời duy nhất câu hỏi: *"Sau khi một Fill xảy ra, trạng thái hiện tại của tài khoản và vị thế là gì?"*.
   - Không quyết định chiến lược, không kiểm soát fill simulation/slippage, không đánh giá Sharpe/MaxDD.

2. **Quy Định Vị Thế Nghiêm Ngặt (No Negative Quantity for Short)**:
   - Vị thế được biểu diễn bằng `PositionSide.LONG` hoặc `PositionSide.SHORT` với `quantity > 0` tuyệt đối. Tuyệt đối **không dùng `quantity = -1`** cho Short.

3. **Xử Lý 5 Vòng Đời Vị Thế (Positions Lifecycle)**:
   - **Open**: Mở mới vị thế Long/Short khi đang Flat.
   - **Increase**: Tăng vị thế cùng chiều, tự động tính giá vào lệnh trung bình trọng số: `(old_qty * old_entry + new_qty * fill_price) / (old_qty + new_qty)`.
   - **Reduce**: Giảm vị thế bán một phần. Giá entry của phần vị thế còn lại giữ nguyên không đổi. Realized PnL được tính trên phần đóng.
   - **Close**: Đóng toàn bộ vị thế. Trạng thái vị thế trở về `None` (Flat).
   - **Reverse**: Đảo chiều vị thế (ví dụ LONG 1 BTC, Fill SELL 2 BTC). Xử lý sạch 2 bước: (1) Đóng vị thế LONG 1 BTC và chốt Realized PnL, (2) Mở mới vị thế SHORT 1 BTC với entry bằng giá fill mới.

4. **Tách Bạch Gross Realized PnL, Fees và Funding**:
   - Gross Realized PnL (`realized_pnl`), Phí giao dịch (`fees_paid`) và Phí funding (`funding_paid`) được quản lý riêng biệt, giúp giữ nguyên PnL gộp cho hệ thống Evaluation và Cost Analysis sau này.
   - `balance = balance + realized_pnl - fees_paid - funding_paid`.
   - `equity = balance + total_unrealized_pnl`.

5. **Pre-Execution Risk Guardrails (`RiskManager`)**:
   - `RiskManager` kiểm tra hạn mức (notional, leverage, position size, shorting permission) **trước khi** order được gửi xuống ExecutionEngine.

---

## Danh Sách Components (`src/portfolio/`)

- **[exceptions.py](file:///d:/reverse_indi/src/portfolio/exceptions.py)**: `PortfolioException`, `InsufficientMarginError`, `InvalidPositionError`, `RiskRejectError`.
- **[account.py](file:///d:/reverse_indi/src/portfolio/account.py)**: Dataclass `Account` (`frozen=True`) quản lý vốn ban đầu, balance, realized PnL, fees paid, funding paid và equity.
- **[position.py](file:///d:/reverse_indi/src/portfolio/position.py)**: Enum `PositionSide` (`LONG`, `SHORT`) và Dataclass bất biến `Position` (`quantity > 0`, `average_entry_price > 0`).
- **[pnl.py](file:///d:/reverse_indi/src/portfolio/pnl.py)**: Các hàm tính toán PnL thuần khiết (`calculate_unrealized_pnl`, `calculate_realized_pnl`).
- **[margin.py](file:///d:/reverse_indi/src/portfolio/margin.py)**: `MarginModel`, `SimpleMarginModel` (`position_notional`, `initial_margin`, `used_margin`, `available_margin`).
- **[risk_manager.py](file:///d:/reverse_indi/src/portfolio/risk_manager.py)**: `RiskManager` kiểm tra rủi ro trước execution (`allow_short`, `max_position_size`, `max_notional`, `max_leverage`).
- **[portfolio_state.py](file:///d:/reverse_indi/src/portfolio/portfolio_state.py)**: Snapshot bất biến `PortfolioState` đóng gói toàn bộ trạng thái tài khoản tại một thời điểm.
- **[portfolio.py](file:///d:/reverse_indi/src/portfolio/portfolio.py)**: Portfolio orchestrator (`apply_fill`, `mark_to_market`, `get_position`, `get_state`).
- **[__init__.py](file:///d:/reverse_indi/src/portfolio/__init__.py)**: Public API export.

---

## Automated Test Suite

Chạy bộ kiểm thử tự động tại `tests/portfolio/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/portfolio -v
```
- **14/14 Unit tests PASS 100%** (Thời gian chạy ~0.001s).
