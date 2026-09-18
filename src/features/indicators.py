"""
[PURPOSE]: Technical Indicators library (ATR, RMA, EMA, Swing Engine).
[DEPENDENCIES]: pandas, numpy.
"""

import pandas as pd
import numpy as np

def calculate_wilder_rma(series: pd.Series, period: int) -> pd.Series:
    """
    [PURPOSE]: Compute Wilder's Smoothing Moving Average (RMA).
    [DEPENDENCIES]: None.
    [ARGS]: series — input price series; period — smoothing window.
    [RETURNS]: RMA Series.
    [SIDE EFFECTS]: None.
    """
    return series.ewm(alpha=1/period, adjust=False).mean()

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    [PURPOSE]: Compute Causal Average True Range (ATR) using Wilder RMA.
    [DEPENDENCIES]: calculate_wilder_rma.
    [ARGS]: df — DataFrame with ['high','low','close']; period — ATR period.
    [RETURNS]: ATR Series.
    [SIDE EFFECTS]: None.
    """
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    tr = np.maximum(high - low, np.maximum((high - close_prev).abs(), (low - close_prev).abs()))
    return calculate_wilder_rma(pd.Series(tr, index=df.index), period)
