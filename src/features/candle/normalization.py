"""Range-relative and optional ATR-relative candle geometry features."""

import numpy as np
import pandas as pd


_ANATOMY_COLUMNS = ("candle_range", "candle_body", "upper_wick", "lower_wick", "low", "close")


def add_candle_normalization(frame: pd.DataFrame, atr_column: str | None = None) -> pd.DataFrame:
    """
    [PURPOSE]: Add normalized candle geometry, optionally relative to a supplied causal ATR column.
    [DEPENDENCIES]: Requires add_candle_anatomy output; optional ATR is owned by the caller's feature pipeline.
    [ARGS]: frame — DataFrame containing anatomy columns; atr_column — optional causal ATR column name.
    [RETURNS]: Copied DataFrame with range ratios and, when requested, ATR-relative geometry columns.
    [SIDE EFFECTS]: Raises ValueError for missing inputs; zero range or nonpositive/invalid ATR yields NaN ratios.
    """
    missing = [column for column in _ANATOMY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Candle normalization requires columns: {', '.join(missing)}.")
    if atr_column is not None and atr_column not in frame.columns:
        raise ValueError(f"Candle normalization ATR column '{atr_column}' is missing.")
    result = frame.copy()
    candle_range = result["candle_range"].astype(float).where(lambda values: values > 0.0)
    result["candle_body_ratio"] = result["candle_body"] / candle_range
    result["upper_wick_ratio"] = result["upper_wick"] / candle_range
    result["lower_wick_ratio"] = result["lower_wick"] / candle_range
    result["close_position"] = (result["close"] - result["low"]) / candle_range
    if atr_column is not None:
        atr = result[atr_column].astype(float).where(lambda values: np.isfinite(values) & (values > 0.0))
        result["candle_range_atr"] = result["candle_range"] / atr
        result["candle_body_atr"] = result["candle_body"] / atr
        result["upper_wick_atr"] = result["upper_wick"] / atr
        result["lower_wick_atr"] = result["lower_wick"] / atr
    return result
