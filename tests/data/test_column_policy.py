"""Column contracts tested exclusively with synthetic in-memory values."""

import unittest
from unittest.mock import patch, mock_open
import pandas as pd
import yaml
from src.data.columns import CANONICAL_COLUMNS, ColumnPolicy, FeatureColumn
from src.data.exceptions import DataValidationError, InvalidDatasetError
from src.data.dataset import Dataset


class TestColumnPolicy(unittest.TestCase):
    def test_explicit_selection_and_feature_type(self):
        """
        [PURPOSE]: Verify exact aliases, feature conversion, ignores and clean index.
        [DEPENDENCIES]: ColumnPolicy.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures logs and asserts synthetic output.
        """
        mapping = {name: name for name in CANONICAL_COLUMNS}
        mapping.update(timestamp="time", volume="Volume")
        policy = ColumnPolicy(mapping, ("note",), {"score": FeatureColumn("raw_score", "float64")})
        raw = pd.DataFrame({name: [1, 2] for name in mapping.values()}, index=[0, 0])
        raw["raw_score"] = ["1.5", "2.5"]
        raw["note"] = ["x", "y"]
        with self.assertLogs("src.data.columns", level="INFO") as logs:
            result = policy.select(raw, "fake:v1")
        self.assertEqual(list(result.columns), list(CANONICAL_COLUMNS) + ["score"])
        self.assertEqual(result.score.tolist(), [1.5, 2.5])
        self.assertEqual(result.index.tolist(), [0, 1])
        self.assertIn("note", "\n".join(logs.output))
        self.assertEqual(ColumnPolicy.from_dict(policy.to_dict()), policy)

    def test_missing_unknown_duplicate_and_nonfinite_rejected(self):
        """
        [PURPOSE]: Prevent arbitrary columns and invalid features from reaching consumers.
        [DEPENDENCIES]: ColumnPolicy.select.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes rejection assertions.
        """
        raw = pd.DataFrame({name: [1.] for name in CANONICAL_COLUMNS})
        for invalid in (raw.drop(columns="open"), raw.assign(secret=1), pd.concat([raw, raw[["open"]]], axis=1)):
            with self.assertRaises(DataValidationError):
                ColumnPolicy().select(invalid, "fake")
        policy = ColumnPolicy(features={"score": FeatureColumn("score", "float64")})
        for value in (None, float("nan"), float("inf"), "bad"):
            with self.subTest(value=value), self.assertRaises(DataValidationError):
                policy.select(raw.assign(score=value), "fake")

    def test_policy_rejects_ambiguity_and_missing_declarations(self):
        """
        [PURPOSE]: Ensure policy errors cannot silently select or discard data.
        [DEPENDENCIES]: ColumnPolicy metadata validators.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes rejection assertions.
        """
        for payload in (None, {}, {"mapping": {}}):
            with self.assertRaises(InvalidDatasetError):
                ColumnPolicy.from_dict(payload)
        for kwargs in ({"ignore": ("open",)}, {"unknown": "drop"},
                       {"features": {"close": FeatureColumn("x", "float64")}}):
            with self.assertRaises(InvalidDatasetError):
                ColumnPolicy(**kwargs)
        with self.assertRaises(InvalidDatasetError):
            FeatureColumn("x", "string")

    def test_policy_copies_mutable_inputs(self):
        """
        [PURPOSE]: Prevent mutation of validated policy through caller dictionaries.
        [DEPENDENCIES]: Frozen ColumnPolicy.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates test-local dictionaries and asserts isolation.
        """
        mapping = {name: name for name in CANONICAL_COLUMNS}
        policy = ColumnPolicy(mapping)
        mapping["open"] = "unexpected"
        self.assertEqual(policy.mapping["open"], "open")
        with self.assertRaises(TypeError):
            policy.mapping["open"] = "changed"

    def test_yaml_requires_explicit_policy_and_preserves_feature_declaration(self):
        """
        [PURPOSE]: Reject missing YAML contracts and parse explicit feature metadata.
        [DEPENDENCIES]: Dataset.from_yaml and mocked YAML file access.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures file calls without accessing disk.
        """
        payload = dict(dataset_id="fake", version="v1",
                       market=dict(venue="binance", symbol="BTCUSDT", quote_currency="USDT"),
                       timeframe="15m", data_range=dict(start="2026-01-01T00:00:00Z", end="2026-01-01T01:00:00Z"),
                       storage_reference=dict(path="never-read.csv", format="csv"), content_hash="0" * 64)
        with patch("builtins.open", mock_open(read_data=yaml.safe_dump(payload))):
            with self.assertRaisesRegex(InvalidDatasetError, "columns requires"):
                Dataset.from_yaml("never-read.yaml")
        policy = ColumnPolicy(features={"score": FeatureColumn("RawScore", "float64")})
        payload["columns"] = policy.to_dict()
        with patch("builtins.open", mock_open(read_data=yaml.safe_dump(payload))):
            dataset = Dataset.from_yaml("never-read.yaml")
        self.assertEqual(dataset.columns, policy)
