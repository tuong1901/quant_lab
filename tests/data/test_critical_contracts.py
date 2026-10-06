"""Critical behavior tests for the strict market-data contract."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.data.compatibility import validate_compatible_datasets
from src.data.dataset import DataRange, Dataset, StorageReference
from src.data.exceptions import DataValidationError, IncompatibleDatasetError, InvalidDatasetError
from src.data.loader import DatasetLoader
from src.data.market import Market
from src.data.timeframe import Timeframe, create_utc_timestamp
from src.data.versioning import calculate_content_hash, canonicalize_ohlcv


class TestCriticalDataContract(unittest.TestCase):
    """Verify invariants that prevent invalid or non-reproducible backtests."""

    def setUp(self) -> None:
        scratch_root = Path.cwd() / ".test-artifacts"
        scratch_root.mkdir(exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=scratch_root)
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.frame = pd.DataFrame(
            {
                "time": pd.date_range(self.start, periods=4, freq="15min"),
                "open": [100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0],
                "close": [101.0, 102.0, 103.0, 104.0],
                "Volume": [10.0, 11.0, 12.0, 13.0],
            }
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _dataset_for(self, frame: pd.DataFrame, name: str = "candles.csv") -> Dataset:
        path = Path(self.temp_dir.name) / name
        frame.to_csv(path, index=False)
        return Dataset(
            dataset_id="btc_m15",
            version="v1",
            market=Market("binance", "btcusdt", "USDT", "perpetual"),
            timeframe=Timeframe.M15,
            data_range=DataRange(self.start, self.start + timedelta(hours=1)),
            storage_reference=StorageReference(str(path), "csv"),
            content_hash=calculate_content_hash(frame),
        )

    def test_market_identity_includes_market_type(self) -> None:
        self.assertNotEqual(
            Market("binance", "BTCUSDT", "USDT", "spot").identity,
            Market("binance", "BTCUSDT", "USDT", "perpetual").identity,
        )

    def test_utc_is_normalized_and_naive_is_rejected(self) -> None:
        normalized = create_utc_timestamp(datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7))))
        self.assertEqual(normalized.utcoffset(), timedelta(0))
        with self.assertRaises(DataValidationError):
            create_utc_timestamp(datetime(2026, 1, 1))

    def test_data_range_is_half_open(self) -> None:
        data_range = DataRange(self.start, self.start + timedelta(minutes=15))
        self.assertLess(self.start, data_range.end)
        with self.assertRaises(InvalidDatasetError):
            DataRange(self.start, self.start)

    def test_hash_is_canonical_and_sensitive_to_values(self) -> None:
        changed = self.frame.copy()
        changed.loc[0, "close"] = 101.01
        self.assertEqual(calculate_content_hash(self.frame), calculate_content_hash(self.frame.copy()))
        self.assertNotEqual(calculate_content_hash(self.frame), calculate_content_hash(changed))

    def test_aliases_are_canonicalized(self) -> None:
        canonical = canonicalize_ohlcv(self.frame)
        self.assertTrue({"timestamp", "open", "high", "low", "close", "volume"}.issubset(canonical.columns))

    def test_open_is_aligned_to_previous_close_after_first_candle(self) -> None:
        unaligned = self.frame.copy()
        unaligned.loc[0, "close"] = 101.5
        unaligned.loc[1, "open"] = 999.0
        canonical = canonicalize_ohlcv(unaligned)
        self.assertEqual(canonical.loc[0, "open"], unaligned.loc[0, "open"])
        self.assertEqual(canonical.loc[1, "open"], canonical.loc[0, "close"])
        self.assertTrue((canonical["open"].iloc[1:].to_numpy() == canonical["close"].iloc[:-1].to_numpy()).all())

    def test_continuity_repair_uses_low_for_a_green_candle(self) -> None:
        unaligned = self.frame.copy()
        unaligned.loc[0, "close"] = 200.0
        unaligned.loc[0, "high"] = 201.0
        unaligned.loc[1, ["open", "high", "low", "close"]] = [101.0, 203.0, 201.0, 202.0]
        canonical = canonicalize_ohlcv(unaligned)
        loaded = DatasetLoader().load(self._dataset_for(unaligned))

        self.assertEqual(canonical.loc[1, "open"], 200.0)
        self.assertEqual(canonical.loc[1, "low"], 200.0)
        self.assertEqual(canonical.loc[1, "high"], 203.0)
        self.assertEqual(loaded.df.loc[1, "open"], 200.0)

    def test_continuity_repair_uses_high_for_a_red_candle(self) -> None:
        unaligned = self.frame.copy()
        unaligned.loc[0, "close"] = 200.0
        unaligned.loc[0, "high"] = 201.0
        unaligned.loc[1, ["open", "high", "low", "close"]] = [101.0, 199.0, 190.0, 195.0]

        canonical = canonicalize_ohlcv(unaligned)

        self.assertEqual(canonical.loc[1, "open"], 200.0)
        self.assertEqual(canonical.loc[1, "high"], 200.0)
        self.assertEqual(canonical.loc[1, "low"], 190.0)

    def test_already_continuous_candle_is_not_changed(self) -> None:
        canonical = canonicalize_ohlcv(self.frame)
        self.assertEqual(canonical.loc[1, "open"], self.frame.loc[1, "open"])
        self.assertEqual(canonical.loc[1, "high"], self.frame.loc[1, "high"])

    def test_loader_accepts_valid_dataset(self) -> None:
        data = DatasetLoader().load(self._dataset_for(self.frame))
        self.assertEqual(len(data.df), 4)

    def test_loader_rejects_missing_required_column(self) -> None:
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(self.frame.drop(columns=["open"])))

    def test_loader_rejects_invalid_ohlc(self) -> None:
        invalid = self.frame.copy()
        invalid.loc[0, "high"] = 98.0
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_duplicate_timestamp(self) -> None:
        invalid = self.frame.copy()
        invalid.loc[1, "time"] = invalid.loc[0, "time"]
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_gap(self) -> None:
        invalid = self.frame.copy()
        invalid.loc[2:, "time"] = invalid.loc[2:, "time"] + pd.Timedelta(minutes=15)
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_hash_mismatch(self) -> None:
        dataset = self._dataset_for(self.frame)
        changed = self.frame.copy()
        changed.loc[0, "close"] = 101.01
        changed.to_csv(dataset.storage_reference.path, index=False)
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(dataset)

    def test_yaml_round_trip_and_compatibility_range(self) -> None:
        dataset = self._dataset_for(self.frame)
        yaml_path = Path(self.temp_dir.name) / "dataset.yaml"
        dataset.to_yaml(str(yaml_path))
        reloaded = Dataset.from_yaml(str(yaml_path))
        self.assertEqual(reloaded.identity, dataset.identity)
        non_overlapping = Dataset(
            dataset_id="btc_m1",
            version="v1",
            market=dataset.market,
            timeframe=Timeframe.M1,
            data_range=DataRange(self.start + timedelta(days=1), self.start + timedelta(days=1, hours=1)),
            storage_reference=dataset.storage_reference,
            content_hash=dataset.content_hash,
        )
        with self.assertRaises(IncompatibleDatasetError):
            validate_compatible_datasets(dataset, non_overlapping)
