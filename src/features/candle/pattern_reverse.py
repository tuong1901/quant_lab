"""Causal reversal-pattern features derived from candle primitives."""

from dataclasses import dataclass

import pandas as pd


_REQUIRED_COLUMNS = (
    "open", "close", "candle_body_ratio", "upper_wick_ratio",
    "lower_wick_ratio", "close_position", "candle_direction",
)


@dataclass(frozen=True)
class ReversalPatternCriteria:
    """
    [PURPOSE]: Hold continuous inequality thresholds for one reversal-pattern evaluation run.
    [DEPENDENCIES]: Required by add_reversal_patterns; supplied by a strategy, experiment, or demonstration caller.
    [ARGS]: Max body ratio, minimum dominant wick ratio, and bullish/bearish close-position boundaries.
    [RETURNS]: Immutable validated criteria instance.
    [SIDE EFFECTS]: Raises ValueError for values outside [0, 1] or inconsistent close-position boundaries.
    """
    max_body_ratio: float
    min_wick_ratio: float
    bullish_close_position: float
    bearish_close_position: float

    def __post_init__(self) -> None:
        """
        [PURPOSE]: Validate continuous pattern criteria before any candle is classified.
        [DEPENDENCIES]: Called automatically by dataclass construction.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises ValueError for invalid criteria.
        """
        values = (self.max_body_ratio, self.min_wick_ratio, self.bullish_close_position, self.bearish_close_position)
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("Reversal-pattern criteria must be within [0, 1].")
        if self.bearish_close_position > self.bullish_close_position:
            raise ValueError("bearish_close_position cannot exceed bullish_close_position.")


def add_reversal_patterns(
    frame: pd.DataFrame,
    criteria: ReversalPatternCriteria,
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
    result = frame.copy()
    small_body = result["candle_body_ratio"] <= criteria.max_body_ratio
    result["bullish_pin_bar"] = (
        small_body
        & (result["lower_wick_ratio"] >= criteria.min_wick_ratio)
        & (result["close_position"] >= criteria.bullish_close_position)
        & (result["candle_direction"] >= 0)
    ).fillna(False).astype(bool)
    result["bearish_pin_bar"] = (
        small_body
        & (result["upper_wick_ratio"] >= criteria.min_wick_ratio)
        & (result["close_position"] <= criteria.bearish_close_position)
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
