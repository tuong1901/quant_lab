"""
[PURPOSE]: Standardized Dataset container for quantitative backtesting.
[DEPENDENCIES]: pandas.
"""

import pandas as pd
from dataclasses import dataclass

@dataclass
class MarketDataset:
    symbol: str
    timeframe: str
    df: pd.DataFrame
