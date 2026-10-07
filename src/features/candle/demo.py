"""Run with: python -m src.features.candle.demo."""

import pandas as pd

from src.features.candle import ReversalPatternCriteria, add_candle_anatomy, add_candle_normalization, add_reversal_patterns

DEMO_REVERSAL_CRITERIA = ReversalPatternCriteria(0.30, 0.50, 0.70, 0.30)


def build_demo_frame() -> pd.DataFrame:
    """
    [PURPOSE]: Build deterministic example candles that expose anatomy and reversal-pattern features.
    [DEPENDENCIES]: Used by the candle demo and visualization modules.
    [ARGS]: None.
    [RETURNS]: DataFrame containing illustrative OHLC and causal ATR values.
    [SIDE EFFECTS]: None.
    """
    return pd.DataFrame([
        {"name": "bearish base", "open": 105.0, "high": 106.0, "low": 99.0, "close": 100.0, "atr": 10.0},
        {"name": "bullish engulfing", "open": 99.0, "high": 110.0, "low": 98.0, "close": 108.0, "atr": 10.0},
        {"name": "bullish pin", "open": 100.0, "high": 106.0, "low": 80.0, "close": 105.0, "atr": 10.0},
        {"name": "bearish pin", "open": 105.0, "high": 130.0, "low": 99.0, "close": 100.0, "atr": 10.0},
        {"name": "doji", "open": 100.0, "high": 104.0, "low": 96.0, "close": 100.0, "atr": 10.0},
        {"name": "zero range", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "atr": 10.0},
    ])


def main() -> None:
    """
    [PURPOSE]: Print full candle features with explicit demonstration criteria.
    [DEPENDENCIES]: Candle anatomy, normalization, reversal patterns, and build_demo_frame.
    [ARGS]: None.
    [RETURNS]: None.
    [SIDE EFFECTS]: Writes a table to stdout.
    """
    featured = add_reversal_patterns(add_candle_normalization(add_candle_anatomy(build_demo_frame()), "atr"), DEMO_REVERSAL_CRITERIA)
    print(featured.to_string(index=False))


if __name__ == "__main__":
    main()
