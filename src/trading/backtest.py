"""
Backtest Orchestration and Historical Simulation Subsystem (`src/trading/backtest.py`).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable
import numpy as np
import pandas as pd

from src.data.timeframe import validate_utc_timestamp
from src.trading.execution.order import Order, OrderSide, OrderType, OrderStatus, OrderId
from src.trading.execution.fill import Fill
from src.trading.execution.broker import ExecutionEngine
from src.trading.execution.fees import PercentageFeeModel
from src.trading.execution.slippage import FixedSlippageModel
from src.trading.portfolio.portfolio import Portfolio, PortfolioState
from src.trading.portfolio.position import PositionSide
from src.trading.portfolio.risk import calculate_risk_position_size
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction
from src.strategies.strategy import Strategy
from src.strategies.state_machine import SetupStateMachine
from src.strategies.atr_ratchet import ATRRatchetExit


from src.data.exceptions import QuantSystemError


# ============================================================================
# Exceptions
# ============================================================================

class BacktestError(QuantSystemError):
    """
    [PURPOSE]: Base exception for all simulation and backtesting errors.
    [DEPENDENCIES]: Inherits from QuantSystemError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: BacktestError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class BacktestExecutionError(BacktestError):
    """
    [PURPOSE]: Raised when order execution or bar processing fails during simulation.
    [DEPENDENCIES]: Inherits from BacktestError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: BacktestExecutionError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class InvalidSimulationStateError(BacktestError):
    """
    [PURPOSE]: Raised when simulation state is corrupt or violates causal invariants.
    [DEPENDENCIES]: Inherits from BacktestError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: InvalidSimulationStateError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class EnvironmentError(BacktestError):
    """
    [PURPOSE]: Base exception for runtime environment errors.
    [DEPENDENCIES]: Inherits from BacktestError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: EnvironmentError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class EnvironmentConstructionError(EnvironmentError):
    """
    [PURPOSE]: Raised when runtime environment or context construction fails.
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: EnvironmentConstructionError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class MissingDependencyError(EnvironmentError):
    """
    [PURPOSE]: Raised when a required component is missing in the environment or registry.
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: MissingDependencyError instance.
    [SIDE EFFECTS]: None.
    """
    pass


class EnvironmentValidationError(EnvironmentError):
    """
    [PURPOSE]: Raised when validation on an environment state fails.
    [DEPENDENCIES]: Inherits from EnvironmentError.
    [ARGS]: Standard exception arguments.
    [RETURNS]: EnvironmentValidationError instance.
    [SIDE EFFECTS]: None.
    """
    pass


# ============================================================================
# Temporal Clock Abstraction
# ============================================================================

@runtime_checkable
class Clock(Protocol):
    """
    [PURPOSE]: Protocol defining contract for reading system or simulated time.
    [DEPENDENCIES]: Used by Strategy, Execution, and Backtest engines.
    """
    def now(self) -> datetime:
        """Return current timestamp (UTC aware)."""
        ...


class HistoricalClock:
    """
    [PURPOSE]: Deterministic simulated clock for historical backtesting and event replay.
    [DEPENDENCIES]: Uses validate_utc_timestamp and BacktestError.
    [ARGS]: start_time — Initial simulated datetime (must be UTC aware, default 2020-01-01).
    [RETURNS]: HistoricalClock instance.
    [SIDE EFFECTS]: Maintains internal simulated timestamp.
    """

    def __init__(self, start_time: Optional[datetime] = None) -> None:
        if start_time is None:
            start_time = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
        self._current_time = validate_utc_timestamp(start_time)

    def now(self) -> datetime:
        """
        [PURPOSE]: Get current simulation timestamp.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: datetime in UTC.
        [SIDE EFFECTS]: None.
        """
        return self._current_time

    def set(self, dt: datetime) -> None:
        """
        [PURPOSE]: Set simulation timestamp to a specific datetime.
        [DEPENDENCIES]: Calls validate_utc_timestamp.
        [ARGS]: dt (datetime).
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates internal _current_time.
        """
        self._current_time = validate_utc_timestamp(dt)

    def advance_to(self, dt: datetime) -> None:
        """
        [PURPOSE]: Monotonically advance simulation clock forward.
        [DEPENDENCIES]: Calls validate_utc_timestamp; raises BacktestError on backward step.
        [ARGS]: dt (datetime).
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates internal _current_time.
        """
        target_dt = validate_utc_timestamp(dt)
        if target_dt < self._current_time:
            raise BacktestError(
                f"Cannot advance HistoricalClock backward in time: target {target_dt} < current {self._current_time}"
            )
        self._current_time = target_dt


class RealtimeClock:
    """
    [PURPOSE]: Wall-clock provider for paper and live trading.
    [DEPENDENCIES]: Standard datetime.
    [ARGS]: None.
    [RETURNS]: RealtimeClock instance.
    [SIDE EFFECTS]: None.
    """

    def now(self) -> datetime:
        """
        [PURPOSE]: Return current wall-clock UTC time.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: datetime in UTC.
        [SIDE EFFECTS]: None.
        """
        return datetime.now(timezone.utc)


# ============================================================================
# Runtime Composition & Context
# ============================================================================

class Registry:
    """
    [PURPOSE]: Maintain an isolated key-value store for optional dynamic runtime dependencies.
    [DEPENDENCIES]: Uses EnvironmentConstructionError and MissingDependencyError.
    [ARGS]: None.
    [RETURNS]: Registry instance.
    [SIDE EFFECTS]: Stores dependencies in internal dict.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, Any] = {}

    def register(self, key: str, val: Any) -> None:
        """
        [PURPOSE]: Register a dynamic dependency under a unique key.
        [DEPENDENCIES]: None.
        [ARGS]: key (str), val (Any).
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises EnvironmentConstructionError if key already exists.
        """
        if key in self._storage:
            raise EnvironmentConstructionError(f"Duplicate registry key detected: '{key}'")
        self._storage[key] = val

    def get(self, key: str, default: Any = None) -> Any:
        """
        [PURPOSE]: Retrieve a registered dependency by key, returning default if absent.
        [DEPENDENCIES]: None.
        [ARGS]: key (str), default (Any).
        [RETURNS]: Dependency value or default.
        [SIDE EFFECTS]: None.
        """
        return self._storage.get(key, default)

    def contains(self, key: str) -> bool:
        """
        [PURPOSE]: Check whether key exists in registry.
        [DEPENDENCIES]: None.
        [ARGS]: key (str).
        [RETURNS]: bool.
        [SIDE EFFECTS]: None.
        """
        return key in self._storage

    def require(self, key: str) -> Any:
        """
        [PURPOSE]: Retrieve a required dependency by key, raising MissingDependencyError if missing.
        [DEPENDENCIES]: None.
        [ARGS]: key (str).
        [RETURNS]: Any dependency value.
        [SIDE EFFECTS]: Raises MissingDependencyError if key not found.
        """
        if key not in self._storage:
            raise MissingDependencyError(f"Required registry key '{key}' was not found.")
        return self._storage[key]


@dataclass(frozen=True)
class ExecutionContext:
    """
    [PURPOSE]: Lightweight contextual metadata during strategy backtest execution.
    [DEPENDENCIES]: Used by BacktestEngine.
    [ARGS]: clock, run, dataset_id, execution_id.
    [RETURNS]: ExecutionContext instance.
    [SIDE EFFECTS]: Raises EnvironmentConstructionError if any field is None.
    """
    clock: Any
    run: Any
    dataset_id: Any
    execution_id: Any

    def __post_init__(self) -> None:
        fields = {
            "clock": self.clock,
            "run": self.run,
            "dataset_id": self.dataset_id,
            "execution_id": self.execution_id,
        }
        for name, val in fields.items():
            if val is None:
                raise EnvironmentConstructionError(
                    f"ExecutionContext field '{name}' cannot be None."
                )


@dataclass(frozen=True)
class Environment:
    """
    [PURPOSE]: Immutable runtime environment container grouping system dependencies.
    [DEPENDENCIES]: clock, market_data, execution, portfolio, config, registry.
    [ARGS]: clock, market_data, execution, portfolio, config, registry.
    [RETURNS]: Environment instance.
    [SIDE EFFECTS]: Raises MissingDependencyError if any field is None.
    """
    clock: Any
    market_data: Any
    execution: Any
    portfolio: Any
    config: Any
    registry: Registry

    def __post_init__(self) -> None:
        fields = {
            "clock": self.clock,
            "market_data": self.market_data,
            "execution": self.execution,
            "portfolio": self.portfolio,
            "config": self.config,
            "registry": self.registry,
        }
        for field_name, field_val in fields.items():
            if field_val is None:
                raise MissingDependencyError(
                    f"Environment field '{field_name}' cannot be None."
                )


class EnvironmentFactory:
    """
    [PURPOSE]: Factory service responsible for constructing clean Environment runtime instances.
    [DEPENDENCIES]: HistoricalClock, ExecutionEngine, Portfolio, Registry, Environment.
    [ARGS]: None.
    [RETURNS]: Environment instance via create().
    [SIDE EFFECTS]: None.
    """

    @classmethod
    def create(
        cls,
        config: Any,
        clock: Optional[Any] = None,
        market_data: Optional[Any] = None,
        execution_engine: Optional[Any] = None,
        portfolio: Optional[Any] = None,
    ) -> Environment:
        """
        [PURPOSE]: Assemble and wire an Environment instance from typed config or injected components.
        [DEPENDENCIES]: Instantiates default components if not provided.
        [ARGS]: config (Any), clock (Optional[Any]), market_data (Optional[Any]), execution_engine (Optional[Any]), portfolio (Optional[Any]).
        [RETURNS]: Fully constructed Environment instance.
        [SIDE EFFECTS]: Raises EnvironmentConstructionError if config is None.
        """
        if config is None:
            raise EnvironmentConstructionError("Configuration parameter 'config' cannot be None.")

        if clock is None:
            start_time = getattr(getattr(config, "time", None), "start", None)
            clock = HistoricalClock(start_time=start_time)

        if market_data is None:
            from src.data.loader import DatasetLoader
            market_data = DatasetLoader()

        if execution_engine is None:
            fee_cfg = getattr(getattr(config, "execution", None), "fee", None)
            maker_rate = getattr(fee_cfg, "maker", 0.0001) if fee_cfg else 0.0001
            taker_rate = getattr(fee_cfg, "taker", 0.0002) if fee_cfg else 0.0002
            fee_model = PercentageFeeModel(maker_bps=maker_rate * 10000.0, taker_bps=taker_rate * 10000.0)

            slip_cfg = getattr(getattr(config, "execution", None), "slippage", None)
            slip_val = getattr(slip_cfg, "value", 0.0002) if slip_cfg else 0.0002
            slippage_model = FixedSlippageModel(slippage_bps=slip_val * 10000.0)

            execution_engine = ExecutionEngine(
                slippage_model=slippage_model,
                fee_model=fee_model,
            )

        if portfolio is None:
            initial_cap = 10000.0
            leverage = 1.0
            if hasattr(config, "portfolio") and config.portfolio is not None:
                if hasattr(config.portfolio, "account") and config.portfolio.account is not None:
                    initial_cap = getattr(config.portfolio.account, "initial_capital", 10000.0)
                if hasattr(config.portfolio, "leverage") and config.portfolio.leverage is not None:
                    leverage = getattr(config.portfolio.leverage, "value", 1.0)
            portfolio = Portfolio(initial_capital=initial_cap, leverage=leverage)

        registry = Registry()

        return Environment(
            clock=clock,
            market_data=market_data,
            execution=execution_engine,
            portfolio=portfolio,
            config=config,
            registry=registry,
        )


# ============================================================================
# Progress & Snapshot Containers
# ============================================================================

@dataclass
class BacktestState:
    """
    [PURPOSE]: Mutable container tracking backtest simulation loop execution progress.
    [DEPENDENCIES]: Used internally by BacktestEngine.
    [ARGS]: current_timestamp, bars_processed, signals, orders, fills, portfolio_states.
    [RETURNS]: BacktestState instance.
    [SIDE EFFECTS]: None.
    """
    current_timestamp: Optional[datetime] = None
    bars_processed: int = 0
    signals: List[Signal] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)
    portfolio_states: List[PortfolioState] = field(default_factory=list)


@dataclass(frozen=True)
class BacktestResult:
    """
    [PURPOSE]: Immutable snapshot containing complete execution history of a backtest run.
    [DEPENDENCIES]: Order, Fill, Signal, PortfolioState.
    [ARGS]: run_id, strategy_id, dataset_id, initial_capital, bars_processed, final_timestamp, signals, orders, fills, portfolio_history, final_portfolio.
    [RETURNS]: BacktestResult instance.
    [SIDE EFFECTS]: Validates UTC final_timestamp.
    """
    run_id: str
    strategy_id: str
    dataset_id: str
    initial_capital: float
    bars_processed: int
    final_timestamp: datetime
    signals: Tuple[Signal, ...]
    orders: Tuple[Order, ...]
    fills: Tuple[Fill, ...]
    portfolio_history: Tuple[PortfolioState, ...]
    final_portfolio: PortfolioState

    def __post_init__(self) -> None:
        validate_utc_timestamp(self.final_timestamp)

    @property
    def final_equity(self) -> float:
        """[RETURNS]: Final equity value from final portfolio state."""
        return self.final_portfolio.equity

    @property
    def realized_pnl(self) -> float:
        """[RETURNS]: Total realized PnL across simulation."""
        return self.final_portfolio.realized_pnl

    @property
    def total_fees(self) -> float:
        """[RETURNS]: Total fees paid across simulation."""
        return self.final_portfolio.fees_paid


# ============================================================================
# Pure Simulation Fast Engine
# ============================================================================

def run_trade_simulation(
    df: pd.DataFrame,
    atr_series: np.ndarray,
    swings_tuple: Tuple[np.ndarray, np.ndarray, np.ndarray],
    params: Dict[str, Any],
    fixed_config: Dict[str, Any],
    fill_mode: str = 'bar_close'
) -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """
    [PURPOSE]: Execute complete backtest simulation over candle dataset for given hyperparameter set.
    [DEPENDENCIES]: SetupStateMachine, ATRRatchetExit, calculate_risk_position_size.
    [ARGS]: df (pd.DataFrame), atr_series (np.ndarray), swings_tuple (Tuple), params (Dict), fixed_config (Dict), fill_mode (str).
    [RETURNS]: Tuple[List[Dict[str, Any]], np.ndarray] -> (trades_list, equity_curve).
    [SIDE EFFECTS]: None (pure functional calculation).
    """
    n = len(df)
    if n == 0:
        return [], np.array([])

    opens = df['open'].to_numpy()
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()

    swing_highs, swing_lows, confirmed_at = swings_tuple

    capital_cfg = fixed_config.get('capital_management', {}) if isinstance(fixed_config, dict) else {}
    friction_cfg = fixed_config.get('friction', {}) if isinstance(fixed_config, dict) else {}

    init_cap = capital_cfg.get('initial_capital', 10000.0)
    initial_capital = float(init_cap[0] if isinstance(init_cap, (list, tuple)) else init_cap)

    r_pct = capital_cfg.get('risk_per_trade_pct', 0.01)
    risk_pct = float(r_pct[0] if isinstance(r_pct, (list, tuple)) else r_pct)

    c_bps = friction_cfg.get('commission_bps', 4.0)
    comm_rate = float(c_bps[0] if isinstance(c_bps, (list, tuple)) else c_bps) / 10000.0

    s_fac = friction_cfg.get('slippage_atr_factor', 0.05)
    slip_factor = float(s_fac[0] if isinstance(s_fac, (list, tuple)) else s_fac)

    use_funding = bool(friction_cfg.get('enable_funding_rate', True))

    f_8h = friction_cfg.get('funding_rate_8h', 0.0001)
    funding_8h = float(f_8h[0] if isinstance(f_8h, (list, tuple)) else f_8h)

    stage_timeout = params.get('stage_timeout_bars', 24)
    buffer_k = params.get('zone_buffer_k', 0.5)
    trigger_type = params.get('trigger_candle_type', 'any')
    ratchet_trigger = params.get('ratchet_activation_trigger', 'at_1R')

    ratchet_cfg = fixed_config.get('atr_ratchet', {}) if isinstance(fixed_config, dict) else {}
    mult_raw = ratchet_cfg.get('multiplier', 3.0)
    ratchet_mult = float(mult_raw[0] if isinstance(mult_raw, (list, tuple)) else mult_raw)

    state_machine = SetupStateMachine(timeout_bars=stage_timeout)
    atr_exit = ATRRatchetExit(multiplier=ratchet_mult)

    current_balance = initial_capital
    trades: List[Dict[str, Any]] = []
    equity_curve = np.zeros(n)
    equity_curve[0] = initial_capital

    in_position = False
    pos_direction = None
    pos_entry_price = 0.0
    pos_stop_loss = 0.0
    pos_lot_size = 0.0
    pos_entry_bar = 0

    for i in range(n):
        c_bar = {'open': opens[i], 'high': highs[i], 'low': lows[i], 'close': closes[i]}
        curr_atr = atr_series[i]

        sh = swing_highs[i] if not np.isnan(swing_highs[i]) else closes[i] * 1.05
        sl = swing_lows[i] if not np.isnan(swing_lows[i]) else closes[i] * 0.95
        eq_price = (sh + sl) / 2.0

        if not in_position:
            stage, direction, trigger_price = state_machine.update_bar(
                c_bar, curr_atr, eq_price, trigger_type, buffer_k
            )

            if stage == 4 and trigger_price is not None:
                slippage = slip_factor * curr_atr
                if fill_mode == 'wick_touch':
                    raw_entry = trigger_price
                else:
                    raw_entry = closes[i]

                if direction == 'long':
                    pos_entry_price = raw_entry + slippage
                else:
                    pos_entry_price = raw_entry - slippage

                pos_stop_loss = atr_exit.initialize_stop(pos_entry_price, direction, curr_atr, ratchet_trigger)
                pos_lot_size = calculate_risk_position_size(current_balance, risk_pct, pos_entry_price, pos_stop_loss)

                if pos_lot_size > 0:
                    in_position = True
                    pos_direction = direction
                    pos_entry_bar = i

        else:
            updated_stop = atr_exit.update_ratchet(
                highs[i], lows[i], closes[i], pos_direction, curr_atr, pos_entry_price, ratchet_trigger
            )
            pos_stop_loss = updated_stop

            is_stopped = False
            exit_price = 0.0

            if pos_direction == 'long' and lows[i] <= pos_stop_loss:
                is_stopped = True
                exit_price = pos_stop_loss - (slip_factor * curr_atr)
            elif pos_direction == 'short' and highs[i] >= pos_stop_loss:
                is_stopped = True
                exit_price = pos_stop_loss + (slip_factor * curr_atr)

            if is_stopped:
                bars_held = i - pos_entry_bar

                if pos_direction == 'long':
                    pnl_raw = (exit_price - pos_entry_price) * pos_lot_size
                else:
                    pnl_raw = (pos_entry_price - exit_price) * pos_lot_size

                notional = (pos_entry_price + exit_price) * 0.5 * pos_lot_size
                comm_cost = notional * comm_rate * 2.0

                funding_cycles = bars_held / 32.0 if use_funding else 0.0
                funding_cost = notional * funding_8h * funding_cycles

                net_pnl = pnl_raw - comm_cost - funding_cost
                r_multiple = net_pnl / (current_balance * risk_pct) if risk_pct > 0 else 0.0

                current_balance += net_pnl

                trade_record = {
                    'entry_bar': pos_entry_bar,
                    'exit_bar': i,
                    'bars_held': bars_held,
                    'direction': pos_direction,
                    'entry_price': pos_entry_price,
                    'exit_price': exit_price,
                    'lot_size': pos_lot_size,
                    'gross_pnl': pnl_raw,
                    'comm_cost': comm_cost,
                    'funding_cost': funding_cost,
                    'net_pnl': net_pnl,
                    'r_multiple': r_multiple,
                    'balance_after': current_balance
                }
                trades.append(trade_record)

                in_position = False
                pos_direction = None
                atr_exit = ATRRatchetExit(multiplier=ratchet_mult)

        equity_curve[i] = current_balance

    return trades, equity_curve


# ============================================================================
# Causal T+1 Simulation Loop Orchestrator
# ============================================================================

class BacktestEngine:
    """
    [PURPOSE]: Simulation Loop Orchestrator running causal T+1 backtesting.
    [DEPENDENCIES]: Strategy, ExecutionEngine, Portfolio, HistoricalClock.
    [ARGS]: strategy, portfolio, broker, clock, environment, context, default_order_quantity, run, kwargs.
    [RETURNS]: BacktestEngine instance.
    [SIDE EFFECTS]: None.
    """

    def __init__(
        self,
        strategy: Optional[Strategy] = None,
        environment: Optional[Any] = None,
        context: Optional[ExecutionContext] = None,
        default_order_quantity: float = 1.0,
        run: Optional[Any] = None,
        portfolio: Optional[Portfolio] = None,
        broker: Optional[Any] = None,
        clock: Optional[Clock] = None,
        **kwargs,
    ):
        if environment is not None:
            self.environment = environment
            self.portfolio = environment.portfolio
            self.execution = environment.execution
            self.clock = getattr(environment, "clock", clock or HistoricalClock())
        else:
            self.environment = None
            self.portfolio = portfolio if portfolio is not None else Portfolio()
            self.execution = broker if broker is not None else ExecutionEngine()
            self.clock = clock if clock is not None else HistoricalClock()

        self.strategy = strategy
        if context is None:
            class DefaultRun:
                run_id = "BTCUSDT"
            target_run = run if run is not None else DefaultRun()
            class DefaultContext:
                clock = self.clock
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
        """
        [PURPOSE]: Execute causal T+1 backtest simulation loop over DataFrame.
        [DEPENDENCIES]: ExecutionEngine, Portfolio, Strategy, HistoricalClock.
        [ARGS]: df (pd.DataFrame).
        [RETURNS]: BacktestResult audit record.
        [SIDE EFFECTS]: Mutates internal portfolio and execution state; raises BacktestError if df empty.
        """
        if df.empty:
            raise BacktestError("DataFrame for backtest is empty.")

        n_bars = len(df)
        portfolio = self.portfolio
        exec_engine = self.execution
        clock = self.clock
        run_id = self._get_run_id()

        window = getattr(getattr(self.context, "run", None), "window", None)
        exec_start = getattr(window, "execution_start", None) if window else None
        exec_end = getattr(window, "execution_end", None) if window else None

        signals = []
        orders = []
        fills = []
        portfolio_states = []
        self.partial_signals = signals
        self.partial_orders = orders
        self.partial_fills = fills
        self.partial_portfolio_states = portfolio_states
        self.partial_start_timestamp = None
        self.partial_last_timestamp = None

        for i in range(n_bars):
            row = df.iloc[i]
            ts = row["timestamp"] if "timestamp" in row else row.name
            if isinstance(ts, str):
                ts = pd.to_datetime(ts, utc=True).to_pydatetime()
            if self.partial_start_timestamp is None:
                self.partial_start_timestamp = ts
            self.partial_last_timestamp = ts

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
