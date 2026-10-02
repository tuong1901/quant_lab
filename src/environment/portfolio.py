"""
Portfolio State Management Orchestrator (`src/environment/portfolio.py`).
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List

from src.core.types import PositionSide, validate_utc_timestamp
from src.engine.fill import Fill
from src.engine.order import OrderSide
from src.environment.account import Account
from src.environment.position import Position
from src.environment.pnl import calculate_realized_pnl, calculate_unrealized_pnl
from src.environment.margin import SimpleMarginModel, MarginState
from src.environment.portfolio_state import PortfolioState
from src.environment.exceptions import DuplicateFillError, InvalidPositionError


class Portfolio:
    """
    [PURPOSE]: Orchestrator for managing position lifecycles, accounting, and MTM updates.
    """

    def __init__(self, initial_capital: float = 10000.0, leverage: float = 1.0):
        self.account = Account(initial_capital=initial_capital, balance=initial_capital)
        self.positions: Dict[str, Position] = {}
        self.margin_model = SimpleMarginModel(leverage=leverage)
        self.processed_fill_ids: set = set()
        self.last_update_time = datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.mark_prices: Dict[str, float] = {}

    @property
    def initial_capital(self) -> float:
        return self.account.initial_capital

    def apply_fill(self, fill: Fill) -> PortfolioState:
        """[PURPOSE]: Process fill across 5 position lifecycle stages."""
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
        else:
            if fill.quantity < existing_pos.quantity:
                realized_pnl = calculate_realized_pnl(existing_pos.side, existing_pos.average_entry_price, fill.price, fill.quantity)
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
                del self.positions[sym]
            else:
                realized_pnl = calculate_realized_pnl(existing_pos.side, existing_pos.average_entry_price, fill.price, existing_pos.quantity)
                reversal_qty = fill.quantity - existing_pos.quantity
                self.positions[sym] = Position(
                    symbol=sym,
                    side=fill_side,
                    quantity=reversal_qty,
                    average_entry_price=fill.price,
                )

        self.account = self.account.with_fill(realized_pnl_delta=realized_pnl, fee=fill.fee)
        return self.get_state(timestamp=fill.timestamp)

    def mark_to_market(
        self,
        timestamp: Optional[datetime] = None,
        mark_prices: Optional[Dict[str, float]] = None,
        symbol: Optional[str] = None,
        mark_price: Optional[float] = None,
    ) -> PortfolioState:
        """[PURPOSE]: Update mark-to-market prices and unrealized PnL."""
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
        """[PURPOSE]: Generate immutable PortfolioState snapshot."""
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
