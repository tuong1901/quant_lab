# Architecture Guard Test Suite (`tests/architecture/`)

## Purpose
The Architecture Guard Test Suite turns the system's architectural boundaries, layer responsibility rules, and dependency direction matrix into automated, repeatable tests.

It enforces strict separation of concerns across `src/` modules, ensuring that zero architectural erosion occurs as features, strategies, or models are added.

---

## Architecture Rules & Test Modules

| Test File | Checked Domain / Layer | Primary Architectural Rule |
| :--- | :--- | :--- |
| [`test_dependency_direction.py`](file:///d:/reverse_indi/tests/architecture/test_dependency_direction.py) | Full System AST Static Analysis | Internal module imports must adhere to the `ALLOWED_DEPENDENCIES` DAG matrix. |
| [`test_strategy_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_strategy_boundary.py) | `src/strategies/` | Strategy logic is decision-only, produces `Signal` objects, and has zero side effects or state mutations. |
| [`test_execution_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_execution_boundary.py) | `src/execution/` | Execution models are stateless order-to-fill translators with non-negative pricing semantics. |
| [`test_portfolio_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_portfolio_boundary.py) | `src/portfolio/` | Accounting invariants: cash, equity, position sizing, and margin state integrity. |
| [`test_backtest_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_backtest_boundary.py) | `src/backtest/` | Simulation engine orchestrates generic `Strategy` protocol without hardcoding concrete strategies. |
| [`test_environment_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_environment_boundary.py) | `src/environment/` | Composition container isolation: state changes in one instance do not pollute others. |
| [`test_evaluation_boundary.py`](file:///d:/reverse_indi/tests/architecture/test_evaluation_boundary.py) | `src/evaluation/` | Performance evaluator is strictly read-only on `BacktestResult`. |
| [`test_contract.py`](file:///d:/reverse_indi/tests/architecture/test_contract.py) | 10-Layer System Contract | End-to-end simulation flow validation across all 10 architectural domains. |

---

## How to Run Tests

```bash
python -m unittest discover -s tests/architecture
```
