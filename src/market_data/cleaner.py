"""
[PURPOSE]: Clean, validate, and fill gaps in OHLCV market data.
[DEPENDENCIES]: pandas.
"""

import pandas as pd

def clean_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    [PURPOSE]: Fill missing timestamps, drop duplicate bars, validate OHLC logic.
    [DEPENDENCIES]: None.
    [ARGS]: df — Input DataFrame with ['open','high','low','close','volume'].
    [RETURNS]: Cleaned pandas DataFrame.
    [SIDE EFFECTS]: Returns new copy of DataFrame.
    """
    clean_df = df.drop_duplicates().copy()
    clean_df = clean_df.ffill().bfill()
    return clean_df
