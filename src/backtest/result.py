"""
BacktestResult immutable output container (`src/backtest/result.py`).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, Optional

from src.strategies.signal import Signal
from src.execution.order import Order
from src.execution.fill import Fill
from src.portfolio.portfolio_state import PortfolioState


@dataclass(frozen=True)
class BacktestResult:
    """
    [PURPOSE]: Immutable read-only result container capturing the output facts of a completed backtest simulation.
    [DEPENDENCIES]: Signal, Order, Fill, PortfolioState.
    [ARGS]:
        run_id — Identifier of experiment run.
        strategy_id — Identifier of evaluated strategy.
        dataset_id — Identifier of evaluated dataset.
        initial_capital — Account starting capital.
        bars_processed — Counter of total simulation bars processed.
        final_timestamp — Timestamp of final market bar.
        signals — Immutable tuple of all generated Signal payloads.
        orders — Immutable tuple of all submitted/executed Order objects.
        fills — Immutable tuple of all trade Fill objects generated.
        portfolio_history — Immutable tuple of all PortfolioState snapshots over time.
        final_portfolio — Final PortfolioState snapshot at simulation end.
    [RETURNS]: Frozen BacktestResult instance.
    [SIDE EFFECTS]: None.
    """

    run_id: str
    strategy_id: str
    dataset_id: str
    initial_capital: float
    bars_processed: int
    final_timestamp: Optional[datetime]
    signals: Tuple[Signal, ...]
    orders: Tuple[Order, ...]
    fills: Tuple[Fill, ...]
    portfolio_history: Tuple[PortfolioState, ...]
    final_portfolio: Optional[PortfolioState]

    @property
    def final_cash(self) -> float:
        """
        [PURPOSE]: Return final cash balance from final portfolio snapshot.
        [DEPENDENCIES]: final_portfolio.
        """
        return self.final_portfolio.balance if self.final_portfolio else 0.0

    @property
    def final_equity(self) -> float:
        """
        [PURPOSE]: Return final portfolio equity from final portfolio snapshot.
        [DEPENDENCIES]: final_portfolio.
        """
        return self.final_portfolio.equity if self.final_portfolio else 0.0

    @property
    def realized_pnl(self) -> float:
        """
        [PURPOSE]: Return cumulative gross realized PnL from final portfolio snapshot.
        [DEPENDENCIES]: final_portfolio.
        """
        return self.final_portfolio.realized_pnl if self.final_portfolio else 0.0

    @property
    def total_fees(self) -> float:
        """
        [PURPOSE]: Return cumulative transaction fees paid from final portfolio snapshot.
        [DEPENDENCIES]: final_portfolio.
        """
        return self.final_portfolio.fees_paid if self.final_portfolio else 0.0
