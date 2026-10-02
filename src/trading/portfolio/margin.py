"""
Margin Model Subsystem (`src/trading/portfolio/margin.py`).
"""

from dataclasses import dataclass
from typing import Dict, Optional
from src.trading.portfolio.position import Position
from src.trading.portfolio.exceptions import PortfolioException


@dataclass(frozen=True)
class MarginState:
    """
    [PURPOSE]: Container holding calculated margin metrics for account.
    [DEPENDENCIES]: Used by Portfolio and RiskManager.
    [ARGS]: position_notional, used_margin, available_margin.
    [RETURNS]: MarginState instance.
    [SIDE EFFECTS]: None.
    """
    position_notional: float
    used_margin: float
    available_margin: float


class SimpleMarginModel:
    """
    [PURPOSE]: Calculate initial margin requirement and available margin based on leverage.
    [DEPENDENCIES]: Used by Portfolio orchestrator.
    [ARGS]: leverage (float, default 1.0).
    [RETURNS]: SimpleMarginModel instance.
    [SIDE EFFECTS]: Raises PortfolioException if leverage <= 0.
    """
    def __init__(self, leverage: float = 1.0):
        if leverage <= 0:
            raise PortfolioException(f"Leverage must be strictly positive (> 0), got {leverage}")
        self.leverage = leverage

    def calculate_margin(
        self,
        positions: Dict[str, Position],
        mark_prices: Dict[str, float],
        equity: float
    ) -> MarginState:
        """
        [PURPOSE]: Compute margin metrics for portfolio.
        [DEPENDENCIES]: Called by Portfolio.get_state().
        [ARGS]: positions (Dict[str, Position]), mark_prices (Dict[str, float]), equity (float).
        [RETURNS]: MarginState with position_notional, used_margin, available_margin.
        [SIDE EFFECTS]: None (pure calculation).
        """
        tot_notional = 0.0
        for sym, pos in positions.items():
            price = mark_prices.get(sym, pos.average_entry_price)
            tot_notional += pos.notional(price)

        used_margin = tot_notional / self.leverage
        available_margin = max(0.0, equity - used_margin)

        return MarginState(
            position_notional=tot_notional,
            used_margin=used_margin,
            available_margin=available_margin,
        )

    def calculate_initial_margin(self, position_notional: float, leverage: Optional[float] = None) -> float:
        """
        [PURPOSE]: Compute required initial margin for a given notional value.
        [DEPENDENCIES]: Used in order pre-trade checks.
        [ARGS]: position_notional (float), leverage (Optional[float]).
        [RETURNS]: float initial margin required.
        [SIDE EFFECTS]: None.
        """
        lev = leverage if leverage is not None else self.leverage
        return position_notional / lev
