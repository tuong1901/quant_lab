"""
[PURPOSE]: Abstract Base Strategy Class for all trading strategies.
[DEPENDENCIES]: core.events.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional

class BaseStrategy(ABC):
    """
    [PURPOSE]: Standard strategy interface for signal generation.
    [DEPENDENCIES]: None.
    """
    def __init__(self, name: str, params: dict):
        self.name = name
        self.params = params

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Optional[dict]:
        """
        [PURPOSE]: Process market data bar and produce trade signal.
        [DEPENDENCIES]: None.
        [ARGS]: df — OHLCV DataFrame up to current bar index.
        [RETURNS]: Optional signal dictionary.
        [SIDE EFFECTS]: None.
        """
        pass
