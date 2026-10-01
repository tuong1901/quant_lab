"""
Timeframe Enum & Utility Functions (`src/data/timeframe.py`).
"""

from enum import Enum
from src.data.exceptions import DataValidationError


class Timeframe(Enum):
    """
    [PURPOSE]: Enum representing standardized candle bar timeframes.
    """
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    def to_seconds(self) -> int:
        """[RETURNS]: Duration of timeframe bar in seconds."""
        mapping = {
            Timeframe.M1: 60,
            Timeframe.M5: 300,
            Timeframe.M15: 900,
            Timeframe.M30: 1800,
            Timeframe.H1: 3600,
            Timeframe.H4: 14400,
            Timeframe.D1: 86400,
        }
        return mapping[self]

    def to_minutes(self) -> int:
        """[RETURNS]: Duration of timeframe bar in minutes."""
        return self.to_seconds() // 60

    @classmethod
    def from_string(cls, val: str) -> "Timeframe":
        """[RETURNS]: Timeframe enum matching string representation."""
        clean = val.lower().strip()
        for tf in cls:
            if tf.value == clean or tf.name.lower() == clean:
                return tf
        raise DataValidationError(f"Unknown timeframe string: '{val}'")
