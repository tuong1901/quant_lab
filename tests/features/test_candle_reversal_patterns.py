"""P0 contracts for causal candle reversal-pattern features."""

import unittest
import pandas as pd

from src.features.candle import add_candle_anatomy, add_candle_normalization, add_reversal_patterns


class TestCandleReversalPatterns(unittest.TestCase):
    """Verify deterministic pin-bar and engulfing feature rules."""

    def _features(self, rows):
        return add_reversal_patterns(add_candle_normalization(add_candle_anatomy(pd.DataFrame(rows))))

    def test_bullish_and_bearish_pin_bars(self):
        result = self._features([
            {"open": 100.0, "high": 106.0, "low": 80.0, "close": 105.0},
            {"open": 105.0, "high": 130.0, "low": 99.0, "close": 100.0},
        ])
        self.assertTrue(result.iloc[0].bullish_pin_bar)
        self.assertTrue(result.iloc[1].bearish_pin_bar)

    def test_engulfing_uses_only_previous_candle_and_preserves_input(self):
        frame = pd.DataFrame([
            {"open": 105.0, "high": 106.0, "low": 99.0, "close": 100.0},
            {"open": 99.0, "high": 110.0, "low": 98.0, "close": 108.0},
        ])
        original = frame.copy(deep=True)
        result = self._features(frame.to_dict("records"))
        self.assertFalse(result.iloc[0].bullish_engulfing)
        self.assertTrue(result.iloc[1].bullish_engulfing)
        pd.testing.assert_frame_equal(frame, original)

