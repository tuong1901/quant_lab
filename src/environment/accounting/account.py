"""
Immutable Account Dataclass Container (`src/environment/account.py`).
"""

from dataclasses import dataclass
from src.environment.exceptions import PortfolioException


@dataclass(frozen=True)
class Account:
    """
    [PURPOSE]: Immutable Account state container.
    """
    initial_capital: float
    balance: float
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    funding_paid: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise PortfolioException(f"Initial capital must be strictly positive (> 0), got {self.initial_capital}.")

    @property
    def equity(self) -> float:
        """[RETURNS]: Account net equity = initial_capital + realized_pnl - fees_paid - funding_paid."""
        return self.initial_capital + self.realized_pnl - self.fees_paid - self.funding_paid

    def with_fill(self, realized_pnl_delta: float, fee: float) -> "Account":
        """[PURPOSE]: Return new Account snapshot after fill."""
        return Account(
            initial_capital=self.initial_capital,
            balance=self.balance + realized_pnl_delta - fee,
            realized_pnl=self.realized_pnl + realized_pnl_delta,
            fees_paid=self.fees_paid + fee,
            funding_paid=self.funding_paid,
        )

    def with_funding(self, funding_fee: float) -> "Account":
        """[PURPOSE]: Return new Account snapshot after funding fee deduction."""
        return Account(
            initial_capital=self.initial_capital,
            balance=self.balance - funding_fee,
            realized_pnl=self.realized_pnl,
            fees_paid=self.fees_paid,
            funding_paid=self.funding_paid + funding_fee,
        )
