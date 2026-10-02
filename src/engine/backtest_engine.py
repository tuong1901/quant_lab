"""
BacktestEngine Causal T+1 Simulation Loop Orchestrator (`src/engine/backtest_engine.py`).
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from src.core.clock import HistoricalClock
from src.core.ids import OrderId, RunId
from src.core.types import validate_utc_timestamp, PositionSide
from src.engine.backtest_result import BacktestResult
from src.engine.exceptions import BacktestError, BacktestExecutionError
from src.engine.execution_engine import ExecutionEngine
from src.engine.order import Order, OrderSide, OrderType, OrderStatus
from src.engine.state import BacktestState
from src.environment.context import ExecutionContext
from src.environment.environment import Environment
from src.environment.portfolio import Portfolio
from src.strategies.context import StrategyContext
from src.strategies.signal import SignalAction
from src.strategies.strategy import Strategy


class BacktestEngine:
    """
    [PURPOSE]: Simulation Loop Orchestrator running causal T+1 backtesting.
    """

    def __init__(
        self,
        environment: Environment,
        strategy: Strategy,
        context: Optional[ExecutionContext] = None,
        default_order_quantity: float = 1.0,
        run: Optional[Any] = None,
        **kwargs,
    ):
        self.environment = environment
        self.strategy = strategy
        if context is None:
            class DefaultRun:
                run_id = "BTCUSDT"
            target_run = run if run is not None else DefaultRun()
            class DefaultContext:
                clock = getattr(environment, "clock", None)
                run = target_run
                dataset_id = "default_dataset"
                execution_id = "default_execution"
            context = DefaultContext()
        self.context = context
        self.default_order_quantity = default_order_quantity
        self.state = BacktestState()

    def _get_run_id(self) -> str:
        if hasattr(self.context, "run"):
            run_obj = self.context.run
            if isinstance(run_obj, str):
                return run_obj
            if hasattr(run_obj, "run_id"):
                return run_obj.run_id
            return str(run_obj)
        return "BTCUSDT"

    def run(self, df: pd.DataFrame) -> BacktestResult:
        """[PURPOSE]: Execute causal T+1 backtest simulation loop over DataFrame."""
        if df.empty:
            raise BacktestError("DataFrame for backtest is empty.")

        n_bars = len(df)
        portfolio = self.environment.portfolio
        exec_engine = self.environment.execution
        clock = self.environment.clock
        run_id = self._get_run_id()

        window = getattr(getattr(self.context, "run", None), "window", None)
        exec_start = getattr(window, "execution_start", None) if window else None
        exec_end = getattr(window, "execution_end", None) if window else None

        signals = []
        orders = []
        fills = []
        portfolio_states = []

        for i in range(n_bars):
            row = df.iloc[i]
            ts = row["timestamp"] if "timestamp" in row else row.name
            if isinstance(ts, str):
                ts = pd.to_datetime(ts, utc=True).to_pydatetime()

            if exec_end is not None and ts > exec_end:
                break

            if isinstance(clock, HistoricalClock):
                clock.advance_to(ts)

            bar_dict = {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 1.0)),
            }

            # 1. Process pending orders from previous bars against Open price of bar T
            exec_results = exec_engine.process_market_data(market_data=bar_dict, timestamp=ts)
            for res in exec_results:
                for f in res.fills:
                    fills.append(f)
                    p_state = portfolio.apply_fill(f)

            # 2. Update mark-to-market at bar Close T
            p_state = portfolio.mark_to_market(timestamp=ts, mark_prices={run_id: bar_dict["close"]})
            portfolio_states.append(p_state)

            # 3. Strategy evaluates Close T and generates signal for T+1
            features = {
                str(col): float(row[col])
                for col in row.index
                if str(col).lower() not in ("open", "high", "low", "close", "volume", "timestamp")
            }
            strat_ctx = StrategyContext(
                timestamp=ts,
                price=bar_dict["close"],
                position_side=p_state.positions.get(run_id).side if run_id in p_state.positions else None,
                features=features,
            )
            sig = self.strategy.on_bar(strat_ctx)
            signals.append(sig)

            # 4. Translate Signal to Order
            if exec_start is not None and ts < exec_start:
                continue

            curr_pos = p_state.positions.get(run_id)
            target_side = sig.action

            if target_side == SignalAction.LONG:
                if curr_pos is None:
                    ord_obj = Order(
                        order_id=OrderId.generate(),
                        symbol=run_id,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=self.default_order_quantity,
                        created_at=ts,
                    )
                    orders.append(ord_obj)
                    exec_engine.submit_order(ord_obj)
                elif curr_pos.side == PositionSide.SHORT:
                    reversal_qty = curr_pos.quantity + self.default_order_quantity
                    ord_obj = Order(
                        order_id=OrderId.generate(),
                        symbol=run_id,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=reversal_qty,
                        created_at=ts,
                    )
                    orders.append(ord_obj)
                    exec_engine.submit_order(ord_obj)
            elif target_side == SignalAction.SHORT:
                if curr_pos is None:
                    ord_obj = Order(
                        order_id=OrderId.generate(),
                        symbol=run_id,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=self.default_order_quantity,
                        created_at=ts,
                    )
                    orders.append(ord_obj)
                    exec_engine.submit_order(ord_obj)
                elif curr_pos.side == PositionSide.LONG:
                    reversal_qty = curr_pos.quantity + self.default_order_quantity
                    ord_obj = Order(
                        order_id=OrderId.generate(),
                        symbol=run_id,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=reversal_qty,
                        created_at=ts,
                    )
                    orders.append(ord_obj)
                    exec_engine.submit_order(ord_obj)

        final_ts = portfolio_states[-1].timestamp if portfolio_states else datetime.now(timezone.utc)

        return BacktestResult(
            run_id=run_id,
            strategy_id=getattr(self.strategy, "strategy_id", "strategy_default"),
            dataset_id=getattr(self.context, "dataset_id", "default_dataset"),
            initial_capital=portfolio.account.initial_capital,
            bars_processed=len(portfolio_states),
            final_timestamp=final_ts,
            signals=tuple(signals),
            orders=tuple(orders),
            fills=tuple(fills),
            portfolio_history=tuple(portfolio_states),
            final_portfolio=portfolio_states[-1] if portfolio_states else portfolio.get_state(final_ts),
        )
