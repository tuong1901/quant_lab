"""
Margin Model Subsystem (`src/environment/margin.py`).
"""

from dataclasses import dataclass
from typing import Dict
from src.environment.position import Position
from src.environment.exceptions import PortfolioException


@dataclass(frozen=True)
class MarginState:
    """
    [PURPOSE]: Container holding calculated margin metrics for account.
    """
    position_notional: float
    used_margin: float
    available_margin: float


class SimpleMarginModel:
    """
    [PURPOSE]: Calculate initial margin requirement and available margin based on leverage.
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
        """[PURPOSE]: Compute margin metrics for portfolio."""
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
        lev = leverage if leverage is not None else self.leverage
        return position_notional / lev
