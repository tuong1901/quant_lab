# Project Status

## What was done
- Tái tạo thành công chỉ báo VIP Multi-Trend Indicator (khớp số học 99.98% với `indicator_vip.pine`).
- Xây dựng hoàn chỉnh **Pipeline Quant Lab: Fibo Zone-Registry + Projection + ATR Ratchet**:
  - `config/`: Tach biệt `zones.yaml`, `fixed_params.yaml`, `search_space.yaml`.
  - `src/`: Codebase 10 modules sạch theo thiết kế SRP (Data Feed, Zone Engine, Projection Engine, 5-Stage State Machine, Fixed ATR Ratchet Exit, Execution Simulator với risk sizing, Purged WFO Splitter, Optuna Plateau Optimizer, Dual-Axis Alpha Decay Tracker, Reporting Engine).
  - CLI Runner `run_pipeline.py`: Hỗ trợ `--benchmark-trials` và `--n-trials` WFO lab.
- Kiểm thử Benchmark: 20 trials hoàn tất trong **3.92 giây** (~196 ms/trial).
- Kiểm thử Full Purged WFO Lab trên dataset M15: hoàn thành phân tích Walk-Forward OOS và xuất kết quả báo cáo định lượng.

## What's next
- Tinh chỉnh `zones.yaml` hoặc thêm các cặp giao dịch / khung thời gian khác nếu muốn thử nghiệm thêm.
- Tùy chỉnh `commission_bps` hoặc `risk_per_trade_pct` theo tài khoản thực tế.

## Open issues / Notes
- None. Toàn bộ pipeline đã sẵn sàng sử dụng và chạy kiểm thử tự động.
