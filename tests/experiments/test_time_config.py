"""
[PURPOSE]: Unit tests for src.experiments.config using standard unittest.
[DEPENDENCIES]: unittest, src.experiments.config.
"""

import unittest
from src.experiments.config import (
    TimeConfig,
    Duration,
    DurationUnit,
    ConfigError,
    parse_duration,
    parse_time_config,
    load_time_config_yaml,
)

class TestTimeConfig(unittest.TestCase):
    def test_parse_duration_valid(self):
        d1 = parse_duration("1y")
        self.assertEqual(d1.value, 1)
        self.assertEqual(d1.unit, DurationUnit.YEARS)

        d2 = parse_duration("6mo")
        self.assertEqual(d2.value, 6)
        self.assertEqual(d2.unit, DurationUnit.MONTHS)

        d3 = parse_duration("30d")
        self.assertEqual(d3.value, 30)
        self.assertEqual(d3.unit, DurationUnit.DAYS)

        d4 = parse_duration("24h")
        self.assertEqual(d4.value, 24)
        self.assertEqual(d4.unit, DurationUnit.HOURS)

        d5 = parse_duration("200bars")
        self.assertEqual(d5.value, 200)
        self.assertEqual(d5.unit, DurationUnit.BARS)

    def test_parse_duration_invalid(self):
        with self.assertRaises(ConfigError):
            parse_duration("abcxyz")

        with self.assertRaises(ConfigError):
            parse_duration("-5d")

        with self.assertRaises(ConfigError):
            parse_duration("100weeks")

    def test_parse_time_config_valid_rolling(self):
        data = {
            "time": {
                "mode": "rolling",
                "anchor": "now",
                "range": {"start": "2024-01-01", "end": "now"},
                "window": {"duration": "1y"},
                "step": {"duration": "1mo"},
                "warmup": {"duration": "200bars"},
                "timezone": "UTC",
                "reproducibility": {"freeze_anchor": True},
            }
        }
        cfg = parse_time_config(data)
        self.assertEqual(cfg.mode, "rolling")
        self.assertEqual(cfg.window_duration, Duration(1, DurationUnit.YEARS))
        self.assertEqual(cfg.step_duration, Duration(1, DurationUnit.MONTHS))
        self.assertEqual(cfg.warmup_duration, Duration(200, DurationUnit.BARS))
        self.assertEqual(cfg.timezone, "UTC")
        self.assertTrue(cfg.freeze_anchor)

    def test_parse_time_config_invalid_mode(self):
        data = {
            "time": {
                "mode": "something_that_does_not_exist",
                "range": {"start": "2024-01-01", "end": "now"},
                "window": {"duration": "1y"},
            }
        }
        with self.assertRaises(ConfigError):
            parse_time_config(data)

    def test_parse_time_config_missing_step_for_rolling(self):
        data = {
            "time": {
                "mode": "rolling",
                "range": {"start": "2024-01-01", "end": "now"},
                "window": {"duration": "1y"},
            }
        }
        with self.assertRaises(ConfigError):
            parse_time_config(data)

    def test_load_yaml_file(self):
        import tempfile
        import os
        yaml_content = """
time:
  mode: rolling
  anchor: now
  range:
    start: '2024-01-01'
    end: now
  window:
    duration: 1y
  step:
    duration: 1mo
  warmup:
    duration: 200bars
  timezone: UTC
  reproducibility:
    freeze_anchor: true
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "time.yaml")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
            cfg = load_time_config_yaml(file_path)
            self.assertEqual(cfg.mode, "rolling")
            self.assertEqual(cfg.window_duration, Duration(1, DurationUnit.YEARS))

if __name__ == "__main__":
    unittest.main()

