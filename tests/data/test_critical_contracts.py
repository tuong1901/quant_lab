"""Critical behavior tests for the strict market-data contract."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open

import pandas as pd

from src.data.compatibility import validate_compatible_datasets
from src.data.dataset import DataRange, Dataset, StorageReference
from src.data.exceptions import DataValidationError, IncompatibleDatasetError, InvalidDatasetError
from src.data.loader import DatasetLoader
from src.data.market import Market
from src.data.timeframe import Timeframe, create_utc_timestamp
from src.data.versioning import calculate_content_hash, canonicalize_ohlcv
from src.data.columns import CANONICAL_COLUMNS, ColumnPolicy


class TestCriticalDataContract(unittest.TestCase):
    """Verify invariants that prevent invalid or non-reproducible backtests."""

    def setUp(self) -> None:
        """
        [PURPOSE]: setUp using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        self.storage = {}
        exists = patch("src.data.loader.Path.is_file", return_value=True)
        reader = patch("src.data.loader.pd.read_csv", side_effect=lambda path: self.storage[str(path)].copy())
        exists.start()
        reader.start()
        self.addCleanup(exists.stop)
        self.addCleanup(reader.stop)
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.frame = pd.DataFrame(
            {
                "timestamp": pd.date_range(self.start, periods=4, freq="15min"),
                "open": [100.0, 101.0, 102.0, 103.0],
                "high": [102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0],
                "close": [101.0, 102.0, 103.0, 104.0],
                "volume": [10.0, 11.0, 12.0, 13.0],
            }
        )

    def _dataset_for(self, frame: pd.DataFrame, name: str = "candles.csv") -> Dataset:
        """
        [PURPOSE]:  dataset for using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: frame — synthetic raw data; name — virtual storage key.
        [RETURNS]: Synthetic Dataset descriptor.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        path = Path(name)
        self.storage[str(path)] = frame.copy()
        try:
            digest = calculate_content_hash(frame)
        except DataValidationError:
            # Invalid raw content must reach the loader, rather than making a
            # rejection test pass prematurely in its fixture hash calculation.
            digest = "0" * 64
        return Dataset(
            dataset_id="btc_m15",
            version="v1",
            market=Market("binance", "btcusdt", "USDT", "perpetual"),
            timeframe=Timeframe.M15,
            data_range=DataRange(self.start, self.start + timedelta(hours=1)),
            storage_reference=StorageReference(str(path), "csv"),
            content_hash=digest,
        )

    def test_market_identity_includes_market_type(self) -> None:
        """
        [PURPOSE]: test market identity includes market type using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        self.assertNotEqual(
            Market("binance", "BTCUSDT", "USDT", "spot").identity,
            Market("binance", "BTCUSDT", "USDT", "perpetual").identity,
        )

    def test_utc_is_normalized_and_naive_is_rejected(self) -> None:
        """
        [PURPOSE]: test utc is normalized and naive is rejected using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        normalized = create_utc_timestamp(datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7))))
        self.assertEqual(normalized.utcoffset(), timedelta(0))
        with self.assertRaises(DataValidationError):
            create_utc_timestamp(datetime(2026, 1, 1))

    def test_data_range_is_half_open(self) -> None:
        """
        [PURPOSE]: test data range is half open using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        data_range = DataRange(self.start, self.start + timedelta(minutes=15))
        self.assertLess(self.start, data_range.end)
        with self.assertRaises(InvalidDatasetError):
            DataRange(self.start, self.start)

    def test_hash_is_canonical_and_sensitive_to_values(self) -> None:
        """
        [PURPOSE]: test hash is canonical and sensitive to values using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        changed = self.frame.copy()
        changed.loc[0, "close"] = 101.01
        self.assertEqual(calculate_content_hash(self.frame), calculate_content_hash(self.frame.copy()))
        self.assertNotEqual(calculate_content_hash(self.frame), calculate_content_hash(changed))

    def test_aliases_are_canonicalized(self) -> None:
        """
        [PURPOSE]: test aliases are canonicalized using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        mapping = {name: name for name in CANONICAL_COLUMNS}
        mapping.update(timestamp="time", volume="Volume")
        source = self.frame.rename(columns={"timestamp": "time", "volume": "Volume"})
        canonical = canonicalize_ohlcv(source, ColumnPolicy(mapping))
        self.assertTrue({"timestamp", "open", "high", "low", "close", "volume"}.issubset(canonical.columns))

    def test_open_is_aligned_to_previous_close_after_first_candle(self) -> None:
        """
        [PURPOSE]: test open is aligned to previous close after first candle using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        unaligned = self.frame.copy()
        unaligned.loc[0, "close"] = 101.5
        unaligned.loc[1, "open"] = 999.0
        canonical = canonicalize_ohlcv(unaligned)
        self.assertEqual(canonical.loc[0, "open"], unaligned.loc[0, "open"])
        self.assertEqual(canonical.loc[1, "open"], canonical.loc[0, "close"])
        self.assertTrue((canonical["open"].iloc[1:].to_numpy() == canonical["close"].iloc[:-1].to_numpy()).all())

    def test_continuity_repair_uses_low_for_a_green_candle(self) -> None:
        """
        [PURPOSE]: test continuity repair uses low for a green candle using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
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
        """
        [PURPOSE]: test continuity repair uses high for a red candle using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        unaligned = self.frame.copy()
        unaligned.loc[0, "close"] = 200.0
        unaligned.loc[0, "high"] = 201.0
        unaligned.loc[1, ["open", "high", "low", "close"]] = [101.0, 199.0, 190.0, 195.0]

        canonical = canonicalize_ohlcv(unaligned)

        self.assertEqual(canonical.loc[1, "open"], 200.0)
        self.assertEqual(canonical.loc[1, "high"], 200.0)
        self.assertEqual(canonical.loc[1, "low"], 190.0)

    def test_already_continuous_candle_is_not_changed(self) -> None:
        """
        [PURPOSE]: test already continuous candle is not changed using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        canonical = canonicalize_ohlcv(self.frame)
        self.assertEqual(canonical.loc[1, "open"], self.frame.loc[1, "open"])
        self.assertEqual(canonical.loc[1, "high"], self.frame.loc[1, "high"])

    def test_loader_accepts_valid_dataset(self) -> None:
        """
        [PURPOSE]: test loader accepts valid dataset using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        data = DatasetLoader().load(self._dataset_for(self.frame))
        self.assertEqual(len(data.df), 4)

    def test_loader_rejects_missing_required_column(self) -> None:
        """
        [PURPOSE]: test loader rejects missing required column using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(self.frame.drop(columns=["open"])))

    def test_loader_rejects_invalid_ohlc(self) -> None:
        """
        [PURPOSE]: test loader rejects invalid ohlc using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        invalid = self.frame.copy()
        invalid.loc[0, "high"] = 98.0
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_duplicate_timestamp(self) -> None:
        """
        [PURPOSE]: test loader rejects duplicate timestamp using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        invalid = self.frame.copy()
        invalid.loc[1, "timestamp"] = invalid.loc[0, "timestamp"]
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_gap(self) -> None:
        """
        [PURPOSE]: test loader rejects gap using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        invalid = self.frame.copy()
        invalid.loc[2:, "timestamp"] = invalid.loc[2:, "timestamp"] + pd.Timedelta(minutes=15)
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(self._dataset_for(invalid))

    def test_loader_rejects_hash_mismatch(self) -> None:
        """
        [PURPOSE]: test loader rejects hash mismatch using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        dataset = self._dataset_for(self.frame)
        changed = self.frame.copy()
        changed.loc[0, "close"] = 101.01
        self.storage[dataset.storage_reference.path] = changed
        with self.assertRaises(DataValidationError):
            DatasetLoader().load(dataset)

    def test_yaml_round_trip_and_compatibility_range(self) -> None:
        """
        [PURPOSE]: test yaml round trip and compatibility range using synthetic data contracts.
        [DEPENDENCIES]: Strict data APIs and mocked storage boundaries.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Executes validation/assertions with in-memory inputs; no physical data I/O.
        """
        dataset = self._dataset_for(self.frame)
        handle = mock_open()
        with patch("builtins.open", handle), patch("src.data.dataset.Path.mkdir"):
            dataset.to_yaml("never-written.yaml")
        serialized = "".join(call.args[0] for call in handle().write.call_args_list)
        with patch("builtins.open", mock_open(read_data=serialized)):
            reloaded = Dataset.from_yaml("never-read.yaml")
        self.assertEqual(reloaded.identity, dataset.identity)
        self.assertEqual(reloaded.columns, dataset.columns)
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
