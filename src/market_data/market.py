"""
Market Domain Model (`src/market_data/market.py`).

Represents the identity and attributes of a trading market/venue.
"""

from dataclasses import dataclass
from typing import Dict, Any

from src.market_data.exceptions import InvalidMarketError


@dataclass(frozen=True)
class Market:
    """
    [PURPOSE]: Immutable value object representing a specific market identity.
    [DEPENDENCIES]: Imported by Dataset; uses InvalidMarketError for validation.
    [ARGS]:
        venue — Market venue name (e.g. 'binance').
        symbol — Trading pair symbol (e.g. 'BTCUSDT').
        market_type — Type of market (e.g. 'perpetual', 'spot', 'futures').
        quote_currency — Quote currency asset (e.g. 'USDT').
    [RETURNS]: Frozen Market instance.
    [SIDE EFFECTS]: None (immutable).
    """
    venue: str
    symbol: str
    market_type: str
    quote_currency: str

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate market attributes upon creation and normalize strings.
        [DEPENDENCIES]: Called automatically by dataclass __init__.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Normalizes venue, symbol, market_type, quote_currency via object.__setattr__.
        """
        if not self.venue or not isinstance(self.venue, str) or not self.venue.strip():
            raise InvalidMarketError("Market venue must be a non-empty string.")
        if not self.symbol or not isinstance(self.symbol, str) or not self.symbol.strip():
            raise InvalidMarketError("Market symbol must be a non-empty string.")
        if not self.market_type or not isinstance(self.market_type, str) or not self.market_type.strip():
            raise InvalidMarketError("Market market_type must be a non-empty string.")
        if not self.quote_currency or not isinstance(self.quote_currency, str) or not self.quote_currency.strip():
            raise InvalidMarketError("Market quote_currency must be a non-empty string.")

        # Normalize strings to canonical form to avoid venue/symbol formatting mismatch
        object.__setattr__(self, "venue", self.venue.strip().lower())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "market_type", self.market_type.strip().lower())
        object.__setattr__(self, "quote_currency", self.quote_currency.strip().upper())

    @property
    def identity(self) -> str:
        """
        [PURPOSE]: Canonical identity string for the market.
        [DEPENDENCIES]: Combines normalized venue, symbol, market_type, quote_currency.
        [ARGS]: None.
        [RETURNS]: str e.g. "binance:BTCUSDT:perpetual:USDT".
        [SIDE EFFECTS]: None.
        """
        return f"{self.venue}:{self.symbol}:{self.market_type}:{self.quote_currency}"

    def to_dict(self) -> Dict[str, Any]:
        """
        [PURPOSE]: Convert Market object to dictionary representation for serialization.
        [DEPENDENCIES]: Used by catalog and dataset export.
        [ARGS]: None.
        [RETURNS]: Dictionary containing market fields.
        [SIDE EFFECTS]: None.
        """
        return {
            "venue": self.venue,
            "symbol": self.symbol,
            "market_type": self.market_type,
            "quote_currency": self.quote_currency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Market":
        """
        [PURPOSE]: Deserialize dictionary representation into a Market object.
        [DEPENDENCIES]: Uses InvalidMarketError if missing keys.
        [ARGS]: data — Dict containing 'venue', 'symbol', 'market_type', 'quote_currency'.
        [RETURNS]: Market object.
        [SIDE EFFECTS]: None.
        """
        if not isinstance(data, dict):
            raise InvalidMarketError("Market data must be a dictionary.")

        required_keys = {"venue", "symbol", "market_type", "quote_currency"}
        missing = required_keys - set(data.keys())
        if missing:
            raise InvalidMarketError(f"Missing required market fields: {missing}")

        return cls(
            venue=str(data["venue"]),
            symbol=str(data["symbol"]),
            market_type=str(data["market_type"]),
            quote_currency=str(data["quote_currency"]),
        )
