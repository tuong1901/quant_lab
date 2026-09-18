# Time & Experiment Planning Engine (`src/experiments/`)

Module chịu trách nhiệm chuyển đổi khai báo cấu hình thử nghiệm theo thời gian của người dùng thành danh sách các `ExperimentRun` cụ thể, đảm bảo tính bất biến (Immutable), kiểm tra biên ranh giới dữ liệu (`DatasetRange`) và duy trì tính tái tạo kết quả tuyệt đối 100% (**Dimension 1 — Correctness**).

## Danh Sách Components

1. **[config.py](file:///d:/reverse_indi/src/experiments/config.py)**:
   - Parser đọc file [config/experiments/time.yaml](file:///d:/reverse_indi/config/experiments/time.yaml).
   - Chuyển đổi chuỗi thời gian (`1y`, `6mo`, `30d`, `200bars`) thành `Duration` object.
   - Validation cấu hình `TimeConfig` (Mode: fixed, rolling, expanding; Range, Warmup, Anchor).

2. **[window.py](file:///d:/reverse_indi/src/experiments/window.py)**:
   - Immutable Dataclass `TimeWindow` (`frozen=True`) mô tả 1 khoảng thời gian backtest: `warmup_start`, `execution_start`, `execution_end`.
   - Cưỡng chế bất đẳng thức thời gian: `warmup_start <= execution_start < execution_end` và bắt buộc UTC Timezone.

3. **[run.py](file:///d:/reverse_indi/src/experiments/run.py)**:
   - Immutable Dataclass `ExperimentRun` (`frozen=True`) đại diện cho 1 lần thực thi thử nghiệm: `run_id`, `window`, `seed`, `metadata`.

4. **[planner.py](file:///d:/reverse_indi/src/experiments/planner.py)**:
   - `DatasetRange`: Interface trừu tượng khai báo khung dữ liệu đầu vào (`start`, `end`, `timeframe_minutes`). Không phụ thuộc trực tiếp vào định dạng file storage (CSV/Parquet/DB).
   - `TimePlanner`: Bộ não giải quyết anchor `now`, tính toán các cửa sổ `TimeWindow` theo mode (`fixed`, `rolling`, `expanding`), tính số nến warmup, kiểm tra vi phạm ranh giới dataset (`PlanningError`) và sinh danh sách `ExperimentRun[]`.

5. **[__init__.py](file:///d:/reverse_indi/src/experiments/__init__.py)**:
   - Clean Public API export toàn bộ các dataclasses, parser và planner.

## Verification & Unit Tests

Bộ test suite tự động nằm tại `tests/experiments/`:
```bash
.\venv\Scripts\python.exe -m unittest discover -s tests/experiments -v
```
- **14/14 Tests PASS** (Thời gian chạy ~0.004s).
