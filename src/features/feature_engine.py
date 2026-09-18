"""
[PURPOSE]: Feature computation pipeline orchestrator.
[DEPENDENCIES]: pandas.
"""

import pandas as pd

class FeatureEngine:
    """
    [PURPOSE]: Calculate technical features on input market data.
    [DEPENDENCIES]: None.
    """
    def __init__(self):
        self._pipeline = []

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        for func in self._pipeline:
            result = func(result)
        return result
