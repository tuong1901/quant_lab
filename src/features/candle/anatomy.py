"""Causal raw candle geometry and direction primitives."""

import numpy as np
import pandas as pd


_OHLC_COLUMNS = ("open", "high", "low", "close")


def add_candle_anatomy(frame: pd.DataFrame) -> pd.DataFrame:
    """
    [PURPOSE]: Add raw candle geometry and direction columns without changing input OHLCV values.
    [DEPENDENCIES]: Consumed by candle normalization and future price-action patterns.
    [ARGS]: frame — DataFrame with lowercase open, high, low, and close columns.
    [RETURNS]: Copied DataFrame with candle range/body/wicks, direction flags, and body return.
    [SIDE EFFECTS]: Raises ValueError for missing columns or invalid OHLC bounds; does not mutate frame.
    """
    missing = [column for column in _OHLC_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Candle anatomy requires columns: {', '.join(missing)}.")
    result = frame.copy()
    open_price, high, low, close = (result[column].astype(float) for column in _OHLC_COLUMNS)
    if ((high < low) | (high < open_price) | (high < close) | (low > open_price) | (low > close)).any():
        raise ValueError("Candle anatomy requires valid OHLC bounds.")

    result["candle_range"] = high - low
    result["candle_body"] = (close - open_price).abs()
    result["upper_wick"] = high - pd.concat([open_price, close], axis=1).max(axis=1)
    result["lower_wick"] = pd.concat([open_price, close], axis=1).min(axis=1) - low
    result["candle_bullish"] = close > open_price
    result["candle_bearish"] = close < open_price
    result["candle_direction"] = np.sign(close - open_price).astype(int)
    result["candle_body_return"] = (close - open_price).where(open_price != 0.0) / open_price.where(open_price != 0.0)
    return result
