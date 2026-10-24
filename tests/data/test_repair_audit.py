"""Repair, hashing and loader audit tests without filesystem data access."""

from dataclasses import replace
import hashlib
import json
import unittest
from unittest.mock import patch

import pandas as pd

from src.data.columns import ColumnPolicy, FeatureColumn
from src.data.dataset import Dataset, DataRange, StorageReference
from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.loader import DatasetLoader, load_m15_ohlcv
from src.data.versioning import canonicalize_ohlcv, enforce_open_close_continuity, calculate_content_hash, verify_dataset_hash
from src.data.exceptions import DataValidationError


class TestRepairAudit(unittest.TestCase):
    def setUp(self):
        """
        [PURPOSE]: Prepare candles exercising both intentional wick repairs.
        [DEPENDENCIES]: pandas.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes in-memory test fields.
        """
        self.frame = pd.DataFrame(dict(timestamp=pd.date_range("2026-01-01", periods=3, freq="15min", tz="UTC"),
                                      open=[199.,198.,197.], high=[201.,199.,198.], low=[198.,190.,196.],
                                      close=[200.,195.,197.], volume=[1.,2.,3.]))

    def descriptor(self, frame=None, policy=None):
        """
        [PURPOSE]: Build verified metadata for synthetic source content.
        [DEPENDENCIES]: Dataset and calculate_content_hash.
        [ARGS]: frame — optional source; policy — optional column contract.
        [RETURNS]: Dataset.
        [SIDE EFFECTS]: Captures expected repair warnings.
        """
        source = self.frame if frame is None else frame
        policy = ColumnPolicy() if policy is None else policy
        with self.assertLogs("src.data.versioning", level="INFO"):
            digest = calculate_content_hash(source, policy)
        return Dataset("fake", Market("binance", "BTCUSDT", "USDT"), Timeframe.M15,
                       DataRange(self.frame.timestamp.iloc[0], self.frame.timestamp.iloc[-1] + pd.Timedelta(minutes=15)),
                       StorageReference("never-read.csv", "csv"), digest, columns=policy)

    def test_each_public_helper_warns_and_preserves_source(self):
        """
        [PURPOSE]: Ensure direct normalization, repair and hashing cannot repair silently.
        [DEPENDENCIES]: Public versioning functions.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures warnings and asserts source immutability.
        """
        original = self.frame.copy(deep=True)
        for function in (enforce_open_close_continuity, canonicalize_ohlcv, calculate_content_hash):
            with self.subTest(function=function.__name__), self.assertLogs("src.data.versioning", level="WARNING") as logs:
                function(self.frame, dataset_identity="fake:v1")
            repairs = [r for r in logs.output if "candle_repaired" in r]
            self.assertEqual(len(repairs), 2)
            self.assertIn("high=199.0->200.0", repairs[0])
            self.assertIn("low=196.0->195.0", repairs[1])
            self.assertIn("dataset=fake:v1", repairs[0])
            self.assertIn("previous_close=200.0", repairs[0])
        pd.testing.assert_frame_equal(self.frame, original)
        with self.assertLogs("src.data.versioning", level="WARNING"):
            self.assertFalse(verify_dataset_hash(self.frame, "0" * 64))

    def test_loader_logs_once_per_repair_and_summarizes(self):
        """
        [PURPOSE]: Verify real loader validates once without duplicate hash-repair messages.
        [DEPENDENCIES]: Mocked storage boundaries and DatasetLoader.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures logs only.
        """
        dataset = self.descriptor()
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=self.frame), self.assertLogs("src.data", level="INFO") as logs:
            result = DatasetLoader().load(dataset)
        self.assertEqual(sum("candle_repaired" in r for r in logs.output), 2)
        self.assertIn("repaired_candles=2 open=2 high=1 low=1", "\n".join(logs.output))
        self.assertIn("hash_verified=True", "\n".join(logs.output))
        self.assertEqual(result.df.high.iloc[1], 200.)

    def test_adapter_emits_warnings_and_rejects_unknown_columns(self):
        """
        [PURPOSE]: Cover legacy loading without a silent schema or repair bypass.
        [DEPENDENCIES]: load_m15_ohlcv and mocked reader.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures diagnostics and assertions.
        """
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=self.frame), self.assertLogs("src.data", level="WARNING") as logs:
            load_m15_ohlcv("never-read.csv")
        self.assertEqual(sum("candle_repaired" in r for r in logs.output), 2)
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=self.frame.assign(note="x")), self.assertLogs("src.data", level="WARNING"):
            with self.assertRaises(DataValidationError):
                load_m15_ohlcv("never-read.csv")

    def test_duplicate_index_and_clean_candles(self):
        """
        [PURPOSE]: Repair positions independent of labels and avoid warnings for unchanged candles.
        [DEPENDENCIES]: canonicalize_ohlcv.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures log records and checks idempotence.
        """
        frame = self.frame.copy()
        frame.index = [0, 0, 0]
        with self.assertLogs("src.data.versioning", level="INFO"):
            clean = canonicalize_ohlcv(frame)
        self.assertEqual(len(clean), 3)
        with self.assertLogs("src.data.versioning", level="INFO") as logs:
            again = canonicalize_ohlcv(clean)
        self.assertFalse(any("candle_repaired" in line for line in logs.output))
        pd.testing.assert_frame_equal(clean, again)

    def test_feature_integrity_and_loader_output(self):
        """
        [PURPOSE]: Hash declared features and exclude explicitly ignored metadata.
        [DEPENDENCIES]: Feature-aware hash and DatasetLoader.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Runs mocked loads and captures rejection logs.
        """
        policy = ColumnPolicy(ignore=("note",), features={"score": FeatureColumn("raw_score", "float64")})
        raw = self.frame.assign(raw_score=[1.,2.,3.], note="metadata")
        dataset = self.descriptor(raw, policy)
        with self.assertLogs("src.data", level="INFO"):
            self.assertEqual(calculate_content_hash(raw.assign(note="changed"), policy), dataset.content_hash)
            self.assertNotEqual(calculate_content_hash(raw.assign(raw_score=9.), policy), dataset.content_hash)
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=raw), self.assertLogs("src.data", level="INFO"):
            result = DatasetLoader().load(dataset)
        self.assertIn("score", result.df)
        self.assertNotIn("note", result.df)
        self.assertNotIn("raw_score", result.df)
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=raw.assign(raw_score=9.)), self.assertLogs("src.data", level="ERROR"):
            with self.assertRaisesRegex(DataValidationError, "hash mismatch"):
                DatasetLoader().load(dataset)

    def test_ohlcv_hash_retains_v1_serialization(self):
        """
        [PURPOSE]: Compare maintained digest against an independent v1 byte representation.
        [DEPENDENCIES]: hashlib/json and canonicalization.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Captures expected warnings.
        """
        rows = [
            ["2026-01-01T00:00:00Z", "199", "201", "198", "200", "1"],
            ["2026-01-01T00:15:00Z", "200", "200", "190", "195", "2"],
            ["2026-01-01T00:30:00Z", "195", "198", "195", "197", "3"],
        ]
        content = b"ohlcv-v1|timestamp|open|high|low|close|volume\n"
        content += b"".join(json.dumps(row, separators=(",", ":")).encode() + b"\n" for row in rows)
        with self.assertLogs("src.data.versioning", level="WARNING"):
            self.assertEqual(calculate_content_hash(self.frame), hashlib.sha256(content).hexdigest())

    def test_unrepairable_bounds_still_fail(self):
        """
        [PURPOSE]: Prevent repair from masking unrelated OHLC violations.
        [DEPENDENCIES]: Canonicalization validators.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Asserts rejection and captures diagnostics.
        """
        invalid = self.frame.copy()
        invalid.loc[0, "high"] = 0.
        with self.assertLogs("src.data.versioning", level="INFO"):
            with self.assertRaises(DataValidationError):
                canonicalize_ohlcv(invalid)
