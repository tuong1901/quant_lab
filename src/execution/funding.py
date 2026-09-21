"""
[PURPOSE]: Funding rate fee module for Crypto Perpetuals.
[DEPENDENCIES]: abc.
"""

from abc import ABC, abstractmethod

class FundingModel(ABC):
    """
    [PURPOSE]: Abstract base class for 8-hour perp funding rate fee calculations.
    """
    @abstractmethod
    def calculate_funding_fee(self, position_notional: float, funding_rate: float) -> float:
        """
        [PURPOSE]: Calculate funding fee debit/credit for perpetual holdings.
        [ARGS]:
            position_notional — Notional value of open position (price * qty).
            funding_rate — 8h funding rate (e.g. 0.0001 for 0.01%).
        [RETURNS]: Funding fee float (positive = debit, negative = credit).
        """
        pass

class PerpetualFundingModel(FundingModel):
    """
    [PURPOSE]: Standard perpetual funding fee calculator.
    [DEPENDENCIES]: FundingModel.
    """
    def calculate_funding_fee(self, position_notional: float, funding_rate: float) -> float:
        return position_notional * funding_rate
