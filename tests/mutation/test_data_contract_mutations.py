"""Mutation tests proving strict loader rejection of corrupted candle data."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

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
        root = Path.cwd() / ".test-artifacts"
        root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=root)
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.frame = pd.DataFrame({
            "time": pd.date_range(self.start, periods=4, freq="15min"),
            "open": [1.0, 2.0, 3.0, 4.0], "high": [2.0, 3.0, 4.0, 5.0],
            "low": [0.0, 1.0, 2.0, 3.0], "close": [1.5, 2.5, 3.5, 4.5], "volume": [1.0] * 4,
        })

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _load(self, frame: pd.DataFrame) -> None:
        path = Path(self.temp_dir.name) / "mutated.csv"
        frame.to_csv(path, index=False)
        descriptor = Dataset(
            "mutation_m15", Market("binance", "BTCUSDT", "USDT", "perpetual"), Timeframe.M15,
            DataRange(self.start, self.start + timedelta(hours=1)), StorageReference(str(path), "csv"), calculate_content_hash(frame),
        )
        DatasetLoader().load(descriptor)

    def test_mutations_are_rejected(self) -> None:
        """Reject missing schema, non-finite price, invalid OHLC, negative volume and a gap."""
        mutations = []
        mutations.append(self.frame.drop(columns=["close"]))
        non_finite = self.frame.copy(); non_finite.loc[0, "open"] = float("inf"); mutations.append(non_finite)
        invalid_ohlc = self.frame.copy(); invalid_ohlc.loc[0, "high"] = -1.0; mutations.append(invalid_ohlc)
        negative_volume = self.frame.copy(); negative_volume.loc[0, "volume"] = -1.0; mutations.append(negative_volume)
        gap = self.frame.copy(); gap.loc[2:, "time"] += pd.Timedelta(minutes=15); mutations.append(gap)
        low_bound_violation = self.frame.copy(); low_bound_violation.loc[0, "close"] = -100.0; mutations.append(low_bound_violation)
        for mutated in mutations:
            with self.subTest(columns=list(mutated.columns)):
                with self.assertRaises(DataValidationError):
                    self._load(mutated)
