"""
[PURPOSE]: Market Data Loader interface and implementations.
[DEPENDENCIES]: pandas.
"""

import pandas as pd
from typing import Protocol

class DataLoader(Protocol):
    """Interface for loading historical market data."""
    def load_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        ...
