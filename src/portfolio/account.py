"""
[PURPOSE]: Account dataclass managing account-level cash balance, equity, fees, and realized PnL.
[DEPENDENCIES]: dataclasses, src.portfolio.exceptions.
"""

from dataclasses import dataclass
from src.portfolio.exceptions import PortfolioException

@dataclass(frozen=True)
class Account:
    """
    [PURPOSE]: Immutable financial state representation of a trading account.
    [DEPENDENCIES]: PortfolioException.
    [ARGS]:
        initial_capital — Initial starting capital (> 0).
        balance — Current cash balance reflecting realized PnL, fees, and funding.
        realized_pnl — Cumulative gross realized PnL.
        fees_paid — Cumulative transaction fees paid.
        funding_paid — Cumulative funding fees paid/received.
    [RETURNS]: Account instance.
    """
    initial_capital: float
    balance: float
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    funding_paid: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise PortfolioException(f"Initial capital must be positive, got {self.initial_capital}.")

    def compute_equity(self, total_unrealized_pnl: float) -> float:
        """
        [PURPOSE]: Calculate current total account equity = balance + total_unrealized_pnl.
        [ARGS]: total_unrealized_pnl — Sum of unrealized Mark-to-Market PnL across positions.
        [RETURNS]: Float equity.
        """
        return self.balance + total_unrealized_pnl

    def apply_transaction(
        self,
        realized_pnl_delta: float = 0.0,
        fee_delta: float = 0.0,
        funding_delta: float = 0.0
    ) -> "Account":
        """
        [PURPOSE]: Apply trade transaction delta to produce an updated immutable Account.
        [ARGS]:
            realized_pnl_delta — Realized PnL from closed position portion.
            fee_delta — Transaction fee paid.
            funding_delta — Funding fee paid.
        [RETURNS]: New updated Account instance.
        """
        new_realized = self.realized_pnl + realized_pnl_delta
        new_fees = self.fees_paid + fee_delta
        new_funding = self.funding_paid + funding_delta
        new_balance = self.balance + realized_pnl_delta - fee_delta - funding_delta

        return Account(
            initial_capital=self.initial_capital,
            balance=new_balance,
            realized_pnl=new_realized,
            fees_paid=new_fees,
            funding_paid=new_funding,
        )
