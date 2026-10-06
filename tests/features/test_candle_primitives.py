"""P0 contracts for causal candle feature primitives."""

import unittest
import pandas as pd

from src.features.candle import add_candle_anatomy, add_candle_normalization


class TestCandlePrimitives(unittest.TestCase):
    """Verify candle geometry, normalization, input preservation, and causal safety."""

    def test_bullish_geometry_direction_and_normalization(self):
        frame = pd.DataFrame([{"open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0, "atr": 10.0}])
        result = add_candle_normalization(add_candle_anatomy(frame), "atr")
        row = result.iloc[0]
        self.assertEqual((row.candle_range, row.candle_body, row.upper_wick, row.lower_wick), (20.0, 5.0, 5.0, 10.0))
        self.assertTrue(row.candle_bullish)
        self.assertFalse(row.candle_bearish)
        self.assertEqual(row.candle_direction, 1)
        self.assertAlmostEqual(row.candle_body_return, 0.05)
        self.assertAlmostEqual(row.candle_body_ratio + row.upper_wick_ratio + row.lower_wick_ratio, 1.0)
        self.assertAlmostEqual(row.close_position, 0.75)
        self.assertAlmostEqual(row.candle_range_atr, 2.0)

    def test_bearish_doji_zero_range_and_input_preservation(self):
        frame = pd.DataFrame([
            {"open": 105.0, "high": 110.0, "low": 90.0, "close": 100.0},
            {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0},
        ])
        original = frame.copy(deep=True)
        result = add_candle_normalization(add_candle_anatomy(frame))
        self.assertTrue(result.iloc[0].candle_bearish)
        self.assertEqual(result.iloc[0].candle_direction, -1)
        self.assertEqual(result.iloc[1].candle_direction, 0)
        self.assertTrue(pd.isna(result.iloc[1].candle_body_ratio))
        pd.testing.assert_frame_equal(frame, original)

    def test_prefix_features_are_unchanged_by_future_candles(self):
        prefix = pd.DataFrame([{"open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0}])
        extended = pd.concat([prefix, pd.DataFrame([{"open": 100.0, "high": 999999.0, "low": 1.0, "close": 1.0}])], ignore_index=True)
        first = add_candle_normalization(add_candle_anatomy(prefix)).iloc[0]
        second = add_candle_normalization(add_candle_anatomy(extended)).iloc[0]
        self.assertEqual(first.candle_range, second.candle_range)
        self.assertEqual(first.lower_wick_ratio, second.lower_wick_ratio)

