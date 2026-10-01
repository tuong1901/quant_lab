"""
BacktestEngine Causal T+1 Simulation Loop Orchestrator (`src/engine/backtest_engine.py`).
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from src.core.clock import HistoricalClock
from src.core.ids import OrderId, RunId
from src.core.types import validate_utc_timestamp
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

    def __init__(self, environment: Environment, strategy: Strategy, context: ExecutionContext):
        self.environment = environment
        self.strategy = strategy
        self.context = context
        self.state = BacktestState()

    def run(self, df: pd.DataFrame) -> BacktestResult:
        """[PURPOSE]: Execute causal T+1 backtest simulation loop over DataFrame."""
        if df.empty:
            raise BacktestError("DataFrame for backtest is empty.")

        n_bars = len(df)
        portfolio = self.environment.portfolio
        exec_engine = self.environment.execution
        clock = self.environment.clock

        signals = []
        orders = []
        fills = []
        portfolio_states = []

        for i in range(n_bars):
            row = df.iloc[i]
            ts = row["timestamp"] if "timestamp" in row else row.name
            if isinstance(ts, str):
                ts = pd.to_datetime(ts, utc=True).to_pydatetime()

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
            p_state = portfolio.mark_to_market(timestamp=ts, mark_prices={self.context.run.run_id: bar_dict["close"]})
            portfolio_states.append(p_state)

            # 3. Strategy evaluates Close T and generates signal for T+1
            strat_ctx = StrategyContext(
                timestamp=ts,
                price=bar_dict["close"],
                position_side=p_state.positions.get(self.context.run.run_id).side if self.context.run.run_id in p_state.positions else None,
            )
            sig = self.strategy.on_bar(strat_ctx)
            signals.append(sig)

            # 4. Translate Signal to Order
            if sig.action in (SignalAction.LONG, SignalAction.SHORT):
                side = OrderSide.BUY if sig.action == SignalAction.LONG else OrderSide.SELL
                ord_obj = Order(
                    order_id=OrderId.generate(),
                    symbol=self.context.run.run_id,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=1.0,
                    created_at=ts,
                )
                orders.append(ord_obj)
                exec_engine.submit_order(ord_obj)

        final_ts = portfolio_states[-1].timestamp if portfolio_states else datetime.now(timezone.utc)

        return BacktestResult(
            run_id=self.context.run.run_id,
            strategy_id=getattr(self.strategy, "strategy_id", "strategy_default"),
            dataset_id=self.context.dataset_id,
            initial_capital=portfolio.account.initial_capital,
            bars_processed=n_bars,
            final_timestamp=final_ts,
            signals=tuple(signals),
            orders=tuple(orders),
            fills=tuple(fills),
            portfolio_history=tuple(portfolio_states),
            final_portfolio=portfolio_states[-1] if portfolio_states else portfolio.get_state(final_ts),
        )
