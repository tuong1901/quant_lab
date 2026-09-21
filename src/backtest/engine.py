"""
BacktestEngine historical simulation loop orchestrator (`src/backtest/engine.py`).
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd

from src.core.types import validate_utc_timestamp
from src.environment.environment import Environment
from src.strategies.strategy import Strategy
from src.strategies.context import StrategyContext
from src.strategies.signal import SignalAction, Signal
from src.execution.order import Order, OrderSide, OrderType
from src.portfolio.position import PositionSide, Position
from src.experiments.run import ExperimentRun
from src.backtest.state import BacktestState
from src.backtest.exceptions import BacktestExecutionError


class BacktestEngine:
    """
    [PURPOSE]: Orchestrates historical simulation loops over Environment, Strategy, Execution, and Portfolio.
    [DEPENDENCIES]: Environment, Strategy, StrategyContext, Signal, Order, ExecutionEngine, Portfolio, ExperimentRun, BacktestState.
    [ARGS]:
        environment — Active Environment instance containing dependencies.
        strategy — Strategy instance adhering to Strategy Protocol contract.
        run — Optional ExperimentRun configuration holding TimeWindow bounds.
        default_order_quantity — Fixed position sizing quantity for Phase 1 (default 1.0).
    [RETURNS]: BacktestEngine instance.
    [SIDE EFFECTS]: Advances environment clock, submits orders, processes fills, and updates portfolio state.
    """

    def __init__(
        self,
        environment: Environment,
        strategy: Strategy,
        run: Optional[ExperimentRun] = None,
        default_order_quantity: float = 1.0,
    ) -> None:
        """
        [PURPOSE]: Initialize BacktestEngine with dependencies.
        """
        if environment is None:
            raise BacktestExecutionError("BacktestEngine requires a non-null Environment instance.")
        if strategy is None:
            raise BacktestExecutionError("BacktestEngine requires a non-null Strategy instance.")

        self.environment = environment
        self.strategy = strategy
        self.experiment_run = run
        self.default_order_quantity = default_order_quantity
        self._order_counter: int = 0

    def run(self, df: Optional[pd.DataFrame] = None) -> BacktestState:
        """
        [PURPOSE]: Execute the historical backtest simulation loop over a DataFrame.
        [DEPENDENCIES]: Environment, Strategy, ExecutionEngine, Portfolio.
        [ARGS]: df — Optional pandas DataFrame containing OHLCV and feature columns.
        [RETURNS]: BacktestState containing chronological simulation records.
        [SIDE EFFECTS]: Mutates environment subsystems (clock, execution, portfolio).
        """
        if df is None or df.empty:
            raise BacktestExecutionError("DataFrame input 'df' cannot be None or empty.")

        state = BacktestState()
        symbol = "BTCUSDT"
        if hasattr(self.environment, "config") and hasattr(self.environment.config, "strategy_dataset"):
            symbol = getattr(self.environment.config.strategy_dataset, "symbol", "BTCUSDT")

        # Determine time window bounds if ExperimentRun is active
        window = getattr(self.experiment_run, "window", None) if self.experiment_run else None

        for _, row in df.iterrows():
            # 1. Parse timestamp and validate UTC
            raw_ts = row["timestamp"]
            ts = validate_utc_timestamp(raw_ts)

            # Check window boundaries if window is active
            if window is not None:
                if ts < window.warmup_start:
                    continue
                if ts > window.execution_end:
                    break
                is_warmup = (ts < window.execution_start)
            else:
                is_warmup = False

            # 2. Advance historical clock
            if hasattr(self.environment.clock, "advance_to"):
                try:
                    self.environment.clock.advance_to(ts)
                except Exception:
                    if hasattr(self.environment.clock, "set"):
                        self.environment.clock.set(ts)
            elif hasattr(self.environment.clock, "set"):
                self.environment.clock.set(ts)

            # 3. Extract bar prices & features
            open_price = float(row.get("open", row.get("close")))
            high_price = float(row.get("high", row.get("close")))
            low_price = float(row.get("low", row.get("close")))
            close_price = float(row["close"])
            volume_val = float(row.get("volume", 0.0))

            features: Dict[str, float] = {}
            for col in row.index:
                if col.lower() not in ("timestamp", "time", "date", "datetime", "open", "high", "low", "close", "volume"):
                    val = row[col]
                    if isinstance(val, (int, float)) and not pd.isna(val):
                        features[col] = float(val)

            # 4. Read active portfolio position side
            active_pos: Optional[Position] = self.environment.portfolio.positions.get(symbol)
            pos_side: Optional[PositionSide] = None
            if active_pos is not None and active_pos.quantity > 0:
                pos_side = active_pos.side

            # 5. Build StrategyContext & evaluate Strategy
            context = StrategyContext(
                timestamp=ts,
                price=close_price,
                position_side=pos_side,
                features=features,
            )

            signal: Signal = self.strategy.on_bar(context)
            state.signals.append(signal)

            # 6. Signal -> Order translation (Trading period only, skip during warmup)
            if not is_warmup:
                orders = self._translate_signal_to_orders(
                    signal=signal,
                    symbol=symbol,
                    current_price=close_price,
                    timestamp=ts,
                    current_position=active_pos,
                )
                for order in orders:
                    accepted_order = self.environment.execution.submit_order(order)
                    state.orders.append(accepted_order)

            # 7. Process market data tick via ExecutionEngine
            bar_market_data = {
                "timestamp": ts,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume_val,
            }

            exec_results = self.environment.execution.process_market_data(
                market_data=bar_market_data,
                timestamp=ts,
            )

            # 8. Apply Fills to Portfolio
            for res in exec_results:
                for fill in res.fills:
                    p_state = self.environment.portfolio.apply_fill(fill)
                    state.fills.append(fill)

            # 9. Portfolio Mark-to-Market
            p_state = self.environment.portfolio.mark_to_market(
                symbol=symbol,
                mark_price=close_price,
                timestamp=ts,
            )
            state.portfolio_states.append(p_state)

            state.bars_processed += 1
            state.current_timestamp = ts

        return state

    def _translate_signal_to_orders(
        self,
        signal: Signal,
        symbol: str,
        current_price: float,
        timestamp: datetime,
        current_position: Optional[Position],
    ) -> List[Order]:
        """
        [PURPOSE]: Translate Phase 1 Signal directional intent (HOLD, LONG, SHORT) into Order objects.
        [DEPENDENCIES]: Order, SignalAction, PositionSide.
        [ARGS]:
            signal — Strategy Signal object.
            symbol — Symbol identifier.
            current_price — Latest bar price.
            timestamp — Current bar timestamp.
            current_position — Active Position object if present.
        [RETURNS]: List of Order objects to submit to ExecutionEngine.
        [SIDE EFFECTS]: Increments internal order counter.
        """
        if signal.action == SignalAction.HOLD:
            return []

        pos_side: Optional[PositionSide] = None
        pos_qty: float = 0.0
        if current_position is not None and current_position.quantity > 0:
            pos_side = current_position.side
            pos_qty = current_position.quantity

        orders: List[Order] = []

        if signal.action == SignalAction.LONG:
            if pos_side == PositionSide.LONG:
                return []
            elif pos_side is None:
                # Open LONG
                qty = self.default_order_quantity
                self._order_counter += 1
                ord_id = f"ord_{self._order_counter:04d}"
                orders.append(
                    Order(
                        order_id=ord_id,
                        symbol=symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=qty,
                        created_at=timestamp,
                    )
                )
            elif pos_side == PositionSide.SHORT:
                # Reversal: Close SHORT + Open LONG
                qty = pos_qty + self.default_order_quantity
                self._order_counter += 1
                ord_id = f"ord_{self._order_counter:04d}"
                orders.append(
                    Order(
                        order_id=ord_id,
                        symbol=symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=qty,
                        created_at=timestamp,
                    )
                )

        elif signal.action == SignalAction.SHORT:
            if pos_side == PositionSide.SHORT:
                return []
            elif pos_side is None:
                # Open SHORT
                qty = self.default_order_quantity
                self._order_counter += 1
                ord_id = f"ord_{self._order_counter:04d}"
                orders.append(
                    Order(
                        order_id=ord_id,
                        symbol=symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=qty,
                        created_at=timestamp,
                    )
                )
            elif pos_side == PositionSide.LONG:
                # Reversal: Close LONG + Open SHORT
                qty = pos_qty + self.default_order_quantity
                self._order_counter += 1
                ord_id = f"ord_{self._order_counter:04d}"
                orders.append(
                    Order(
                        order_id=ord_id,
                        symbol=symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=qty,
                        created_at=timestamp,
                    )
                )

        return orders
