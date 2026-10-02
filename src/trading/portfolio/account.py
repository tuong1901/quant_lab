"""
Immutable Account Dataclass Container (`src/trading/portfolio/account.py`).
"""

from dataclasses import dataclass
from src.trading.portfolio.exceptions import PortfolioException


@dataclass(frozen=True)
class Account:
    """
    [PURPOSE]: Immutable Account state container.
    [DEPENDENCIES]: Used by Portfolio orchestrator.
    [ARGS]: initial_capital, balance, realized_pnl, fees_paid, funding_paid.
    [RETURNS]: Account instance.
    [SIDE EFFECTS]: None.
    """
    initial_capital: float
    balance: float
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    funding_paid: float = 0.0

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate account initial capital invariant.
        [DEPENDENCIES]: Called automatically on dataclass instantiation.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises PortfolioException if initial_capital <= 0.
        """
        if self.initial_capital <= 0:
            raise PortfolioException(f"Initial capital must be strictly positive (> 0), got {self.initial_capital}.")

    @property
    def equity(self) -> float:
        """
        [PURPOSE]: Compute account net equity.
        [DEPENDENCIES]: Depends on initial_capital, realized_pnl, fees_paid, funding_paid.
        [ARGS]: None.
        [RETURNS]: float equity value.
        [SIDE EFFECTS]: None.
        """
        return self.initial_capital + self.realized_pnl - self.fees_paid - self.funding_paid

    def with_fill(self, realized_pnl_delta: float, fee: float) -> "Account":
        """
        [PURPOSE]: Return new Account snapshot after fill.
        [DEPENDENCIES]: Called by Portfolio.apply_fill.
        [ARGS]: realized_pnl_delta (float), fee (float).
        [RETURNS]: New Account snapshot.
        [SIDE EFFECTS]: None (pure functional update).
        """
        return Account(
            initial_capital=self.initial_capital,
            balance=self.balance + realized_pnl_delta - fee,
            realized_pnl=self.realized_pnl + realized_pnl_delta,
            fees_paid=self.fees_paid + fee,
            funding_paid=self.funding_paid,
        )

    def with_funding(self, funding_fee: float) -> "Account":
        """
        [PURPOSE]: Return new Account snapshot after funding fee deduction.
        [DEPENDENCIES]: Called during funding cycle processing.
        [ARGS]: funding_fee (float).
        [RETURNS]: New Account snapshot.
        [SIDE EFFECTS]: None (pure functional update).
        """
        return Account(
            initial_capital=self.initial_capital,
            balance=self.balance - funding_fee,
            realized_pnl=self.realized_pnl,
            fees_paid=self.fees_paid,
            funding_paid=self.funding_paid + funding_fee,
        )
