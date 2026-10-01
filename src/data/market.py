"""
Immutable Market Value Object (`src/data/market.py`).
"""

from dataclasses import dataclass
from src.data.exceptions import InvalidMarketError


@dataclass(frozen=True)
class Market:
    """
    [PURPOSE]: Immutable dataclass representing exchange venue, symbol and market specification.
    """
    venue: str
    symbol: str
    quote_currency: str
    market_type: str = "PERPETUAL"

    def __post_init__(self) -> None:
        if not self.venue or not isinstance(self.venue, str):
            raise InvalidMarketError("Venue must be a non-empty string.")
        if not self.symbol or not isinstance(self.symbol, str):
            raise InvalidMarketError("Symbol must be a non-empty string.")
        if not self.quote_currency or not isinstance(self.quote_currency, str):
            raise InvalidMarketError("Quote currency must be a non-empty string.")

    @property
    def identity(self) -> str:
        """[RETURNS]: Canonical market string e.g. 'BINANCE:BTCUSDT'."""
        return f"{self.venue.upper()}:{self.symbol.upper()}"
