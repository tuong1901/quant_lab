"""Causal swing-pivot indicator."""

from typing import Tuple

import numpy as np
import pandas as pd


def calculate_causal_swings(
    df: pd.DataFrame, lookback: int = 20
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    [PURPOSE]: Identify swing high and low pivots only once their lookback window has closed.
    [DEPENDENCIES]: Used by consumers that need causally confirmed swing levels.
    [ARGS]: df — DataFrame with high and low columns; lookback — pivot confirmation half-window.
    [RETURNS]: Swing highs, swing lows, and confirmation-bar arrays.
    [SIDE EFFECTS]: None (pure calculation).
    """
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    count = len(highs)

    swing_highs = np.full(count, np.nan)
    swing_lows = np.full(count, np.nan)
    confirmed_at = np.full(count, -1, dtype=int)

    for index in range(lookback, count - lookback):
        high_window = highs[index - lookback : index + lookback + 1]
        low_window = lows[index - lookback : index + lookback + 1]
        confirmation_bar = index + lookback

        if bool(highs[index] == np.max(high_window)):
            swing_highs[confirmation_bar] = highs[index]
            confirmed_at[confirmation_bar] = confirmation_bar
        if bool(lows[index] == np.min(low_window)):
            swing_lows[confirmation_bar] = lows[index]
            confirmed_at[confirmation_bar] = confirmation_bar

    latest_high = np.nan
    latest_low = np.nan
    for index in range(count):
        if not np.isnan(swing_highs[index]):
            latest_high = swing_highs[index]
        if not np.isnan(swing_lows[index]):
            latest_low = swing_lows[index]
        swing_highs[index] = latest_high
        swing_lows[index] = latest_low

    return swing_highs, swing_lows, confirmed_at
