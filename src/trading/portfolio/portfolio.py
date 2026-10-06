"""
Portfolio State Management and Snapshot Container (`src/trading/portfolio/portfolio.py`).
"""

from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass, field

from src.data.timeframe import validate_utc_timestamp
from src.trading.execution.fill import Fill
from src.trading.execution.order import OrderSide
from src.trading.portfolio.account import Account
from src.trading.portfolio.position import Position, PositionSide
from src.trading.portfolio.pnl import calculate_realized_pnl, calculate_unrealized_pnl
from src.trading.portfolio.margin import SimpleMarginModel, MarginState
from src.trading.portfolio.exceptions import DuplicateFillError, InvalidPositionError, PortfolioException
from src.trading.portfolio.trades import ClosedTrade, _OpenTradeCycle


@dataclass(frozen=True)
class PortfolioState:
    """
    [PURPOSE]: Immutable point-in-time snapshot of complete portfolio state.
    [DEPENDENCIES]: Used by RiskManager, BacktestEngine, and Reporting.
    [ARGS]: timestamp, balance, equity, realized_pnl, unrealized_pnl, fees_paid, funding_paid, used_margin, available_margin, positions.
    [RETURNS]: PortfolioState instance.
    [SIDE EFFECTS]: Raises PortfolioException on negative balance or unvalidated timestamp.
    """
    timestamp: datetime
    balance: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    fees_paid: float
    funding_paid: float
    used_margin: float
    available_margin: float
    positions: Dict[str, Position] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate point-in-time state invariants.
        [DEPENDENCIES]: Calls validate_utc_timestamp.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises PortfolioException if balance < 0 or timestamp invalid.
        """
        validate_utc_timestamp(self.timestamp)
        if self.balance < 0:
            raise PortfolioException(f"Balance cannot be negative, got {self.balance}")


class Portfolio:
    """
    [PURPOSE]: Orchestrator for managing position lifecycles, accounting, and MTM updates.
    [DEPENDENCIES]: Interacts with Account, Position, SimpleMarginModel, Fill.
    [ARGS]: initial_capital (float, default 10000.0), leverage (float, default 1.0).
    [RETURNS]: Portfolio instance.
    [SIDE EFFECTS]: None.
    """

    def __init__(self, initial_capital: float = 10000.0, leverage: float = 1.0):
        self.account = Account(initial_capital=initial_capital, balance=initial_capital)
        self.positions: Dict[str, Position] = {}
        self.margin_model = SimpleMarginModel(leverage=leverage)
        self.processed_fill_ids: set = set()
        self.last_update_time = datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.mark_prices: Dict[str, float] = {}
        self._open_trade_cycles: Dict[str, _OpenTradeCycle] = {}
        self._closed_trades: list[ClosedTrade] = []

    @property
    def initial_capital(self) -> float:
        """
        [PURPOSE]: Get account initial capital.
        [DEPENDENCIES]: Delegates to Account.initial_capital.
        [ARGS]: None.
        [RETURNS]: float initial capital.
        [SIDE EFFECTS]: None.
        """
        return self.account.initial_capital

    @property
    def closed_trades(self) -> tuple[ClosedTrade, ...]:
        """
        [PURPOSE]: Expose immutable evidence for all quantities closed by this portfolio.
        [DEPENDENCIES]: Populated by apply_fill and consumed by BacktestResult/evaluation.
        [ARGS]: None.
        [RETURNS]: Tuple of ClosedTrade records in deterministic fill order.
        [SIDE EFFECTS]: None.
        """
        return tuple(self._closed_trades)

    def apply_fill(self, fill: Fill) -> PortfolioState:
        """
        [PURPOSE]: Process fill across 5 position lifecycle stages (New, Add, Partial Close, Exact Close, Reversal).
        [DEPENDENCIES]: Calls calculate_realized_pnl, Account.with_fill.
        [ARGS]: fill (Fill).
        [RETURNS]: Updated PortfolioState.
        [SIDE EFFECTS]: Mutates positions and account state; raises DuplicateFillError if fill_id reprocessed.
        """
        if fill.fill_id in self.processed_fill_ids:
            raise DuplicateFillError(f"Fill ID '{fill.fill_id}' has already been processed.")

        validate_utc_timestamp(fill.timestamp)
        self.processed_fill_ids.add(fill.fill_id)
        self.last_update_time = fill.timestamp
        self.mark_prices[fill.symbol] = fill.price

        sym = fill.symbol
        existing_pos = self.positions.get(sym)
        fill_side = PositionSide.LONG if fill.side == OrderSide.BUY else PositionSide.SHORT

        realized_pnl = 0.0

        if existing_pos is None:
            self.positions[sym] = Position(
                symbol=sym,
                side=fill_side,
                quantity=fill.quantity,
                average_entry_price=fill.price,
            )
            self._open_trade_cycles[sym] = _OpenTradeCycle(
                symbol=sym,
                side=fill_side,
                quantity=fill.quantity,
                entry_timestamp=fill.timestamp,
                average_entry_price=fill.price,
                unallocated_entry_fee=fill.fee,
            )
        elif existing_pos.side == fill_side:
            tot_qty = existing_pos.quantity + fill.quantity
            weighted_entry = (
                (existing_pos.quantity * existing_pos.average_entry_price) + (fill.quantity * fill.price)
            ) / tot_qty
            self.positions[sym] = Position(
                symbol=sym,
                side=fill_side,
                quantity=tot_qty,
                average_entry_price=weighted_entry,
                realized_pnl=existing_pos.realized_pnl,
            )
            cycle = self._open_trade_cycles[sym]
            cycle.average_entry_price = weighted_entry
            cycle.quantity = tot_qty
            cycle.unallocated_entry_fee += fill.fee
        else:
            if fill.quantity < existing_pos.quantity:
                realized_pnl = calculate_realized_pnl(existing_pos.side, existing_pos.average_entry_price, fill.price, fill.quantity)
                self._record_closed_trade(existing_pos, fill, fill.quantity, fill.fee)
                rem_qty = existing_pos.quantity - fill.quantity
                self.positions[sym] = Position(
                    symbol=sym,
                    side=existing_pos.side,
                    quantity=rem_qty,
                    average_entry_price=existing_pos.average_entry_price,
                    realized_pnl=existing_pos.realized_pnl + realized_pnl,
                )
            elif fill.quantity == existing_pos.quantity:
                realized_pnl = calculate_realized_pnl(existing_pos.side, existing_pos.average_entry_price, fill.price, fill.quantity)
                self._record_closed_trade(existing_pos, fill, fill.quantity, fill.fee)
                del self.positions[sym]
            else:
                realized_pnl = calculate_realized_pnl(existing_pos.side, existing_pos.average_entry_price, fill.price, existing_pos.quantity)
                closing_fee = fill.fee * (existing_pos.quantity / fill.quantity)
                self._record_closed_trade(existing_pos, fill, existing_pos.quantity, closing_fee)
                reversal_qty = fill.quantity - existing_pos.quantity
                self.positions[sym] = Position(
                    symbol=sym,
                    side=fill_side,
                    quantity=reversal_qty,
                    average_entry_price=fill.price,
                )
                self._open_trade_cycles[sym] = _OpenTradeCycle(
                    symbol=sym,
                    side=fill_side,
                    quantity=reversal_qty,
                    entry_timestamp=fill.timestamp,
                    average_entry_price=fill.price,
                    unallocated_entry_fee=fill.fee - closing_fee,
                )

        self.account = self.account.with_fill(realized_pnl_delta=realized_pnl, fee=fill.fee)
        return self.get_state(timestamp=fill.timestamp)

    def _record_closed_trade(
        self,
        position: Position,
        closing_fill: Fill,
        closed_quantity: float,
        exit_fee: float,
    ) -> None:
        """
        [PURPOSE]: Allocate open-cycle costs and append one immutable record for a realized quantity.
        [DEPENDENCIES]: Called only by apply_fill before reducing or removing the matching Position.
        [ARGS]: position, closing_fill, closed_quantity, exit_fee.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates the internal open-cycle accumulator and closed-trade evidence list.
        """
        cycle = self._open_trade_cycles[position.symbol]
        if cycle.quantity != position.quantity:
            raise PortfolioException("Trade cycle quantity must match the position before a close.")

        entry_fee = cycle.unallocated_entry_fee * (closed_quantity / cycle.quantity)
        gross_pnl = calculate_realized_pnl(position.side, position.average_entry_price, closing_fill.price, closed_quantity)
        self._closed_trades.append(
            ClosedTrade(
                trade_id=f"{closing_fill.fill_id}:{len(self._closed_trades) + 1}",
                symbol=position.symbol,
                side=position.side,
                quantity=closed_quantity,
                entry_timestamp=cycle.entry_timestamp,
                exit_timestamp=closing_fill.timestamp,
                entry_price=position.average_entry_price,
                exit_price=closing_fill.price,
                gross_pnl=gross_pnl,
                entry_fee=entry_fee,
                exit_fee=exit_fee,
            )
        )
        cycle.quantity -= closed_quantity
        cycle.unallocated_entry_fee -= entry_fee
        if cycle.quantity == 0:
            del self._open_trade_cycles[position.symbol]

    def mark_to_market(
        self,
        timestamp: Optional[datetime] = None,
        mark_prices: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
        mark_price: Optional[float] = None,
    ) -> PortfolioState:
        """
        [PURPOSE]: Update mark-to-market prices and recalculate unrealized PnL for active positions.
        [DEPENDENCIES]: Calls calculate_unrealized_pnl, validate_utc_timestamp.
        [ARGS]: timestamp (Optional[datetime]), mark_prices (Optional[Dict[str, float]]), symbol (Optional[str]), mark_price (Optional[float]).
        [RETURNS]: Updated PortfolioState.
        [SIDE EFFECTS]: Mutates mark_prices and positions in place.
        """
        if symbol is not None and mark_price is not None:
            mp_dict = {symbol: mark_price}
        else:
            mp_dict = mark_prices or {}

        ts = timestamp if timestamp is not None else self.last_update_time
        validate_utc_timestamp(ts)
        self.last_update_time = ts
        self.mark_prices.update(mp_dict)

        updated_positions = {}
        for sym, pos in self.positions.items():
            if sym in self.mark_prices:
                mp = self.mark_prices[sym]
                unrealized = calculate_unrealized_pnl(pos.side, pos.average_entry_price, mp, pos.quantity)
                updated_positions[sym] = pos.with_unrealized_pnl(unrealized)
            else:
                updated_positions[sym] = pos

        self.positions = updated_positions
        return self.get_state(timestamp=ts)

    def get_state(self, timestamp: Optional[datetime] = None) -> PortfolioState:
        """
        [PURPOSE]: Generate immutable PortfolioState snapshot.
        [DEPENDENCIES]: Calls SimpleMarginModel.calculate_margin.
        [ARGS]: timestamp (Optional[datetime]).
        [RETURNS]: PortfolioState snapshot.
        [SIDE EFFECTS]: None.
        """
        ts = timestamp if timestamp is not None else self.last_update_time
        if ts.year == 1970:
            ts = datetime.now(timezone.utc)

        tot_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        curr_equity = self.account.equity + tot_unrealized

        margin_state = self.margin_model.calculate_margin(
            positions=self.positions,
            mark_prices=self.mark_prices,
            equity=curr_equity,
        )

        return PortfolioState(
            timestamp=ts,
            balance=self.account.balance,
            equity=curr_equity,
            realized_pnl=self.account.realized_pnl,
            unrealized_pnl=tot_unrealized,
            fees_paid=self.account.fees_paid,
            funding_paid=self.account.funding_paid,
            used_margin=margin_state.used_margin,
            available_margin=margin_state.available_margin,
            positions=dict(self.positions),
        )
