"""
Immutable Market Value Object (`src/data/market.py`).
"""

from dataclasses import dataclass
from src.data.exceptions import InvalidMarketError


@dataclass(frozen=True)
class Market:
    """
    [PURPOSE]: Represent one canonical tradable market for dataset identity checks.
    [DEPENDENCIES]: InvalidMarketError.
    [ARGS]: venue, symbol, quote_currency, market_type.
    [RETURNS]: Immutable normalized Market value object.
    [SIDE EFFECTS]: Raises InvalidMarketError for missing market fields.
    """
    venue: str
    symbol: str
    quote_currency: str
    market_type: str = "PERPETUAL"

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate and canonicalize all market identity components.
        [DEPENDENCIES]: Called by dataclass initialization.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises InvalidMarketError for invalid fields.
        """
        fields = {
            "venue": self.venue,
            "symbol": self.symbol,
            "quote_currency": self.quote_currency,
            "market_type": self.market_type,
        }
        if any(not isinstance(value, str) or not value.strip() for value in fields.values()):
            raise InvalidMarketError("Market fields must be non-empty strings.")

        object.__setattr__(self, "venue", self.venue.strip().upper())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "quote_currency", self.quote_currency.strip().upper())
        object.__setattr__(self, "market_type", self.market_type.strip().upper())

    @property
    def identity(self) -> str:
        """
        [PURPOSE]: Return a collision-free canonical market identity.
        [DEPENDENCIES]: Normalized Market fields.
        [ARGS]: None.
        [RETURNS]: VENUE:SYMBOL:MARKET_TYPE:QUOTE_CURRENCY.
        [SIDE EFFECTS]: None.
        """
        return f"{self.venue}:{self.symbol}:{self.market_type}:{self.quote_currency}"
