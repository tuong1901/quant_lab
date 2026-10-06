"""Causal reversal-pattern features derived from candle primitives."""

import pandas as pd


_REQUIRED_COLUMNS = (
    "open", "close", "candle_body_ratio", "upper_wick_ratio",
    "lower_wick_ratio", "close_position", "candle_direction",
)


def add_reversal_patterns(
    frame: pd.DataFrame,
    max_body_ratio: float = 0.30,
    min_wick_ratio: float = 0.50,
    bullish_close_position: float = 0.70,
    bearish_close_position: float = 0.30,
) -> pd.DataFrame:
    """
    [PURPOSE]: Add causal bullish/bearish pin-bar and engulfing pattern evidence columns.
    [DEPENDENCIES]: Requires candle anatomy and normalization features from the same or prior bars.
    [ARGS]: frame — OHLC DataFrame with candle primitive columns; remaining arguments — explicit pattern thresholds in [0, 1].
    [RETURNS]: Copied DataFrame with four boolean reversal-pattern columns.
    [SIDE EFFECTS]: Raises ValueError for missing columns or invalid thresholds; does not mutate frame or generate orders.
    """
    missing = [column for column in _REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Reversal patterns require columns: {', '.join(missing)}.")
    if not (0.0 <= max_body_ratio <= 1.0 and 0.0 <= min_wick_ratio <= 1.0):
        raise ValueError("Pattern body and wick thresholds must be within [0, 1].")
    if not (0.0 <= bearish_close_position <= bullish_close_position <= 1.0):
        raise ValueError("Close-position thresholds must satisfy 0 <= bearish <= bullish <= 1.")

    result = frame.copy()
    small_body = result["candle_body_ratio"] <= max_body_ratio
    result["bullish_pin_bar"] = (
        small_body
        & (result["lower_wick_ratio"] >= min_wick_ratio)
        & (result["close_position"] >= bullish_close_position)
        & (result["candle_direction"] >= 0)
    ).fillna(False).astype(bool)
    result["bearish_pin_bar"] = (
        small_body
        & (result["upper_wick_ratio"] >= min_wick_ratio)
        & (result["close_position"] <= bearish_close_position)
        & (result["candle_direction"] <= 0)
    ).fillna(False).astype(bool)

    previous_open = result["open"].shift(1)
    previous_close = result["close"].shift(1)
    result["bullish_engulfing"] = (
        (result["candle_direction"] > 0)
        & (previous_close < previous_open)
        & (result["open"] <= previous_close)
        & (result["close"] >= previous_open)
    ).fillna(False).astype(bool)
    result["bearish_engulfing"] = (
        (result["candle_direction"] < 0)
        & (previous_close > previous_open)
        & (result["open"] >= previous_close)
        & (result["close"] <= previous_open)
    ).fillna(False).astype(bool)
    return result
