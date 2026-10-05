"""Causal Average True Range indicator."""

import numpy as np
import pandas as pd


def calculate_causal_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """
    [PURPOSE]: Compute causal Average True Range using Wilder's RMA method.
    [DEPENDENCIES]: Used by VIP Trend and feature consumers needing ATR values.
    [ARGS]: df — DataFrame containing open, high, low, and close columns; period — RMA lookback.
    [RETURNS]: Array of ATR values aligned to df rows.
    [SIDE EFFECTS]: None (pure calculation).
    """
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    count = len(closes)

    if count == 0:
        return np.array([])

    true_ranges = np.zeros(count)
    true_ranges[0] = highs[0] - lows[0]
    for index in range(1, count):
        true_ranges[index] = max(
            highs[index] - lows[index],
            abs(highs[index] - closes[index - 1]),
            abs(lows[index] - closes[index - 1]),
        )

    atr = np.zeros(count)
    if count < period:
        atr[:] = np.mean(true_ranges)
        return atr

    initial_sma = np.mean(true_ranges[:period])
    atr[:period] = initial_sma
    alpha = 1.0 / float(period)
    current_atr = initial_sma
    for index in range(period, count):
        current_atr = alpha * true_ranges[index] + (1.0 - alpha) * current_atr
        atr[index] = current_atr

    return atr
