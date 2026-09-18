"""
[PURPOSE]: Margin models and MarginState containers for leverage and margin accounting.
[DEPENDENCIES]: abc, dataclasses, src.portfolio.exceptions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.portfolio.exceptions import PortfolioException

@dataclass(frozen=True)
class MarginState:
    """
    [PURPOSE]: Immutable summary of margin usage and availability.
    [ARGS]:
        leverage — Account/position leverage multiplier.
        used_margin — Total margin currently locked for open positions.
        available_margin — Equity minus used_margin available for new trades.
    """
    leverage: float
    used_margin: float
    available_margin: float

class MarginModel(ABC):
    """
    [PURPOSE]: Abstract base class for margin requirement calculations.
    """
    @abstractmethod
    def calculate_initial_margin(self, position_notional: float, leverage: float) -> float:
        """
        [PURPOSE]: Compute initial margin requirement for a position notional.
        [ARGS]:
            position_notional — Notional value (quantity * price).
            leverage — Position leverage.
        [RETURNS]: Float required margin.
        """
        pass

class SimpleMarginModel(MarginModel):
    """
    [PURPOSE]: Standard linear margin model: initial_margin = position_notional / leverage.
    [DEPENDENCIES]: MarginModel, PortfolioException.
    """
    def calculate_initial_margin(self, position_notional: float, leverage: float) -> float:
        if leverage < 1.0:
            raise PortfolioException(f"Leverage must be at least 1.0, got {leverage}.")
        if position_notional < 0:
            raise PortfolioException(f"Position notional cannot be negative, got {position_notional}.")
        return position_notional / leverage
