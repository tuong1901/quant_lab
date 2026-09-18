"""
[PURPOSE]: Purged & Embargoed Walk-Forward Optimization Splitter.
[DEPENDENCIES]: pandas.
"""

import pandas as pd
from typing import List, Tuple

class PurgedWFOSplitter:
    """
    [PURPOSE]: Split time-series dataset into Purged WFO Train/Test windows.
    [DEPENDENCIES]: None.
    """
    def __init__(self, n_windows: int = 3, purge_bars: int = 10, embargo_bars: int = 10):
        self.n_windows = n_windows
        self.purge_bars = purge_bars
        self.embargo_bars = embargo_bars

    def split(self, df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        [PURPOSE]: Generate Train/Test DataFrames with purge & embargo guards.
        [DEPENDENCIES]: None.
        [ARGS]: df — full dataset DataFrame.
        [RETURNS]: List of (train_df, test_df) tuples.
        [SIDE EFFECTS]: None.
        """
        splits = []
        n = len(df)
        window_size = n // (self.n_windows + 1)
        for i in range(self.n_windows):
            train_end = (i + 1) * window_size
            test_end = train_end + window_size
            train_df = df.iloc[:train_end - self.purge_bars]
            test_df = df.iloc[train_end + self.embargo_bars:test_end]
            splits.append((train_df, test_df))
        return splits
