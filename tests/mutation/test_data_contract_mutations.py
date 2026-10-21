"""Mutation tests proving strict loader rejection of corrupted candle data."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from src.data.dataset import DataRange, Dataset, StorageReference
from src.data.exceptions import DataValidationError
from src.data.loader import DatasetLoader
from src.data.market import Market
from src.data.timeframe import Timeframe
from src.data.versioning import calculate_content_hash


class TestDataContractMutations(unittest.TestCase):
    """Mutate a valid fixture one invariant at a time and require rejection."""

    def setUp(self) -> None:
        """
        [PURPOSE]: setUp using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.frame = pd.DataFrame({
            "timestamp": pd.date_range(self.start, periods=4, freq="15min"),
            "open": [1.0, 2.0, 3.0, 4.0], "high": [2.0, 3.0, 4.0, 5.0],
            "low": [0.0, 1.0, 2.0, 3.0], "close": [1.5, 2.5, 3.5, 4.5], "volume": [1.0] * 4,
        })

    def _load(self, frame: pd.DataFrame) -> None:
        """
        [PURPOSE]:  load using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: frame — mutated synthetic data.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        with self.assertLogs("src.data.versioning", level="INFO"):
            expected = calculate_content_hash(self.frame)
        descriptor = Dataset(
            "mutation_m15", Market("binance", "BTCUSDT", "USDT", "perpetual"), Timeframe.M15,
            DataRange(self.start, self.start + timedelta(hours=1)), StorageReference("never-read.csv", "csv"), expected,
        )
        with patch("src.data.loader.Path.is_file", return_value=True), \
             patch("src.data.loader.pd.read_csv", return_value=frame), \
             self.assertLogs("src.data", level="INFO"):
            DatasetLoader().load(descriptor)

    def test_mutations_are_rejected(self) -> None:
        """
        [PURPOSE]: Reject missing schema, non-finite price, invalid OHLC, negative volume and a gap.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        mutations = []
        mutations.append((self.frame.drop(columns=["close"]), "Column policy mismatch"))
        non_finite = self.frame.copy(); non_finite.loc[0, "open"] = float("inf"); mutations.append((non_finite, "finite"))
        invalid_ohlc = self.frame.copy(); invalid_ohlc.loc[0, "high"] = -1.0; mutations.append((invalid_ohlc, "OHLC violation"))
        negative_volume = self.frame.copy(); negative_volume.loc[0, "volume"] = -1.0; mutations.append((negative_volume, "negative volume"))
        gap = self.frame.copy(); gap.loc[2, "timestamp"] += pd.Timedelta(minutes=1); mutations.append((gap, "irregular candles"))
        low_bound_violation = self.frame.copy(); low_bound_violation.loc[0, "close"] = -100.0; mutations.append((low_bound_violation, "OHLC violation"))
        for mutated, expected_error in mutations:
            with self.subTest(columns=list(mutated.columns)):
                with self.assertRaisesRegex(DataValidationError, expected_error):
                    self._load(mutated)
