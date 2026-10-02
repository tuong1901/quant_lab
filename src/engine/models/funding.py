"""
Perpetual Funding Rate Model (`src/engine/funding.py`).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PerpetualFundingModel:
    """
    [PURPOSE]: 8-hour funding rate fee calculator for Crypto Perpetual Futures.
    """
    funding_rate_8h: float = 0.0001

    def calculate_funding_fee(
        self,
        notional_value: Optional[float] = None,
        bars_held: int = 1,
        bar_timeframe_minutes: int = 15,
        position_notional: Optional[float] = None,
        funding_rate: Optional[float] = None,
    ) -> float:
        """[PURPOSE]: Calculate cumulative funding fee over position holding period."""
        notional = position_notional if position_notional is not None else (notional_value or 0.0)
        rate = funding_rate if funding_rate is not None else self.funding_rate_8h
        if notional <= 0:
            return 0.0
        if position_notional is not None and notional_value is None:
            return position_notional * rate
        minutes_held = bars_held * bar_timeframe_minutes
        funding_cycles = minutes_held / 480.0  # 480 minutes = 8 hours
        return notional * rate * funding_cycles
