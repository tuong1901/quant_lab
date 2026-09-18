"""
Timeframe Enum Abstraction (`src/market_data/timeframe.py`).

Provides a unified representation for bar timeframes (1m, 5m, 15m, 30m, 1h, 4h, 1d).
"""

from enum import Enum
from typing import Union

from src.market_data.exceptions import InvalidDatasetError


class Timeframe(str, Enum):
    """
    [PURPOSE]: Standard enum for market data timeframes with string serialization.
    [DEPENDENCIES]: Used by Dataset, DatasetLoader, and FeatureEngine.
    [ARGS]: Standard timeframe value string (e.g. '15m').
    [RETURNS]: Enum value.
    [SIDE EFFECTS]: None.
    """
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    def __str__(self) -> str:
        return self.value

    def to_minutes(self) -> int:
        """
        [PURPOSE]: Convert timeframe enum to equivalent duration in minutes.
        [DEPENDENCIES]: Called by data range calculation and missing candle validation.
        [ARGS]: None.
        [RETURNS]: int minutes.
        [SIDE EFFECTS]: None.
        """
        mapping = {
            Timeframe.M1: 1,
            Timeframe.M5: 5,
            Timeframe.M15: 15,
            Timeframe.M30: 30,
            Timeframe.H1: 60,
            Timeframe.H4: 240,
            Timeframe.D1: 1440,
        }
        return mapping[self]

    def to_seconds(self) -> int:
        """
        [PURPOSE]: Convert timeframe enum to equivalent duration in seconds.
        [DEPENDENCIES]: Called by timedelta validation.
        [ARGS]: None.
        [RETURNS]: int seconds.
        [SIDE EFFECTS]: None.
        """
        return self.to_minutes() * 60

    @classmethod
    def parse(cls, value: Union[str, "Timeframe", int]) -> "Timeframe":
        """
        [PURPOSE]: Deterministically parse various input representations into a canonical Timeframe enum.
        [DEPENDENCIES]: Uses InvalidDatasetError for unparseable formats.
        [ARGS]: value — String ('15m', 'M15', '15min'), integer seconds (900), or Timeframe instance.
        [RETURNS]: Canonical Timeframe enum instance.
        [SIDE EFFECTS]: None.
        """
        if isinstance(value, cls):
            return value

        if isinstance(value, int):
            # Parse by seconds
            for tf in cls:
                if tf.to_seconds() == value:
                    return tf
            raise InvalidDatasetError(f"Unsupported integer seconds timeframe: {value}")

        if not isinstance(value, str):
            raise InvalidDatasetError(f"Timeframe value must be a string, int, or Timeframe enum, got {type(value)}")

        val_clean = value.strip().lower()

        # Handle exact string matches
        for tf in cls:
            if tf.value == val_clean or tf.name.lower() == val_clean:
                return tf

        # Alias mappings
        aliases = {
            "1min": cls.M1,
            "5min": cls.M5,
            "15min": cls.M15,
            "30min": cls.M30,
            "60m": cls.H1,
            "60min": cls.H1,
            "1hour": cls.H1,
            "240m": cls.H4,
            "4hour": cls.H4,
            "1day": cls.D1,
            "24h": cls.D1,
        }

        if val_clean in aliases:
            return aliases[val_clean]

        raise InvalidDatasetError(f"Cannot parse timeframe string: '{value}'")
