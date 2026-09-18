"""
[PURPOSE]: Immutable PortfolioState dataclass representing a complete point-in-time snapshot of portfolio accounting.
[DEPENDENCIES]: dataclasses, datetime, typing, src.portfolio.position.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict
from src.portfolio.position import Position

@dataclass(frozen=True)
class PortfolioState:
    """
    [PURPOSE]: Immutable point-in-time snapshot of full portfolio state.
    [DEPENDENCIES]: Position.
    [ARGS]:
        timestamp — Timezone-aware snapshot timestamp.
        balance — Current account cash balance.
        equity — Total equity (balance + unrealized_pnl).
        realized_pnl — Cumulative gross realized PnL.
        unrealized_pnl — Total mark-to-market unrealized PnL across positions.
        fees_paid — Cumulative transaction fees paid.
        funding_paid — Cumulative funding fees paid/received.
        used_margin — Total margin locked for positions.
        available_margin — Equity minus used_margin.
        positions — Map of symbol to Position instance.
    [RETURNS]: PortfolioState instance.
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
