"""
Unit tests for Market domain model (`src/market_data/market.py`).
"""

import unittest

from src.market_data.market import Market
from src.market_data.exceptions import InvalidMarketError


class TestMarket(unittest.TestCase):
    """
    [PURPOSE]: Verify creation, normalization, validation, and immutability of Market value objects.
    """

    def test_market_creation_and_normalization(self):
        """Test valid Market creation and automatic case normalization."""
        market = Market(
            venue=" Binance ",
            symbol=" btcusdt ",
            market_type=" PERPETUAL ",
            quote_currency=" usdt ",
        )
        self.assertEqual(market.venue, "binance")
        self.assertEqual(market.symbol, "BTCUSDT")
        self.assertEqual(market.market_type, "perpetual")
        self.assertEqual(market.quote_currency, "USDT")
        self.assertEqual(market.identity, "binance:BTCUSDT:perpetual:USDT")

    def test_market_immutability(self):
        """Test that Market attributes cannot be mutated after creation."""
        market = Market("binance", "BTCUSDT", "perpetual", "USDT")
        with self.assertRaises(AttributeError):
            market.symbol = "ETHUSDT"

    def test_market_invalid_fields(self):
        """Test that invalid/empty fields raise InvalidMarketError."""
        with self.assertRaises(InvalidMarketError):
            Market("", "BTCUSDT", "perpetual", "USDT")

        with self.assertRaises(InvalidMarketError):
            Market("binance", "   ", "perpetual", "USDT")

        with self.assertRaises(InvalidMarketError):
            Market("binance", "BTCUSDT", "", "USDT")

        with self.assertRaises(InvalidMarketError):
            Market("binance", "BTCUSDT", "perpetual", None)

    def test_market_to_dict_and_from_dict(self):
        """Test Market serialization and deserialization."""
        market = Market("binance", "BTCUSDT", "perpetual", "USDT")
        d = market.to_dict()
        self.assertEqual(d["venue"], "binance")
        self.assertEqual(d["symbol"], "BTCUSDT")

        reconstructed = Market.from_dict(d)
        self.assertEqual(reconstructed, market)


if __name__ == "__main__":
    unittest.main()
