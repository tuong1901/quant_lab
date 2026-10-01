"""
Perpetual Funding Rate Model (`src/engine/funding.py`).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PerpetualFundingModel:
    """
    [PURPOSE]: 8-hour funding rate fee calculator for Crypto Perpetual Futures.
    """
    funding_rate_8h: float = 0.0001

    def calculate_funding_fee(self, notional_value: float, bars_held: int, bar_timeframe_minutes: int = 15) -> float:
        """[PURPOSE]: Calculate cumulative funding fee over position holding period."""
        if notional_value <= 0 or bars_held <= 0:
            return 0.0
        minutes_held = bars_held * bar_timeframe_minutes
        funding_cycles = minutes_held / 480.0  # 480 minutes = 8 hours
        return notional_value * self.funding_rate_8h * funding_cycles
