"""Strict physical loading and validation for market datasets."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.data.dataset import DataRange, Dataset
from src.data.exceptions import DataValidationError, InvalidDatasetError
from src.data.timeframe import Timeframe
from src.data.versioning import canonicalize_ohlcv, calculate_content_hash


@dataclass(frozen=True)
class MarketData:
    """
    [PURPOSE]: Pair one verified Dataset descriptor with canonical OHLCV data.
    [DEPENDENCIES]: Dataset, pandas.
    [ARGS]: dataset — Verified metadata; df — Canonical OHLCV DataFrame.
    [RETURNS]: Immutable MarketData container.
    [SIDE EFFECTS]: None.
    """

    dataset: Dataset
    df: pd.DataFrame


class DatasetLoader:
    """Read Dataset storage and enforce the complete strict data contract."""

    def load(self, dataset: Dataset) -> MarketData:
        """
        [PURPOSE]: Load a dataset and reject any schema, temporal, OHLCV, hash or gap breach.
        [DEPENDENCIES]: Dataset, canonicalize_ohlcv, calculate_content_hash.
        [ARGS]: dataset — Immutable Dataset descriptor.
        [RETURNS]: Verified MarketData.
        [SIDE EFFECTS]: Reads local storage and raises DataValidationError on contract failure.
        """
        if not isinstance(dataset, Dataset):
            raise InvalidDatasetError(f"Expected Dataset, got {type(dataset)}")
        path = Path(dataset.storage_reference.path)
        if not path.is_file():
            raise DataValidationError(f"Dataset storage not found: {path}")
        try:
            raw = pd.read_csv(path) if dataset.storage_reference.format == "csv" else pd.read_parquet(path)
        except (OSError, ValueError, ImportError) as error:
            raise DataValidationError(f"Unable to read dataset storage {path}: {error}") from error
        frame = canonicalize_ohlcv(raw)
        self._validate_temporal_contract(frame, dataset.data_range, dataset.timeframe)
        self._validate_ohlcv_bounds(frame)
        if calculate_content_hash(frame) != dataset.content_hash:
            raise DataValidationError(f"Content hash mismatch for dataset {dataset.identity}.")
        return MarketData(dataset=dataset, df=frame)

    @staticmethod
    def _validate_temporal_contract(frame: pd.DataFrame, data_range: DataRange, timeframe: Timeframe) -> None:
        """
        [PURPOSE]: Enforce UTC ordering, [start,end) coverage and no-gap candle cadence.
        [DEPENDENCIES]: DataRange, Timeframe, pandas.
        [ARGS]: frame, data_range, timeframe.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises DataValidationError for duplicate, unordered, out-of-range or gapped data.
        """
        timestamps = frame["timestamp"]
        if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
            raise DataValidationError("Timestamps must be unique and strictly increasing.")
        if timestamps.min() < pd.Timestamp(data_range.start) or timestamps.max() >= pd.Timestamp(data_range.end):
            raise DataValidationError("Timestamps must satisfy DataRange [start, end).")
        interval = pd.Timedelta(seconds=timeframe.to_seconds())
        if (timestamps.diff().dropna() != interval).any():
            raise DataValidationError("Dataset contains missing or irregular candles under strict gap policy.")

    @staticmethod
    def _validate_ohlcv_bounds(frame: pd.DataFrame) -> None:
        """
        [PURPOSE]: Validate OHLC bounds and non-negative volume.
        [DEPENDENCIES]: pandas.
        [ARGS]: frame — Canonical OHLCV DataFrame.
        [RETURNS]: None.
        [SIDE EFFECTS]: Raises DataValidationError when an OHLCV invariant fails.
        """
        if (frame["high"] < frame["low"]).any():
            raise DataValidationError("OHLC violation: high < low.")
        if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
            raise DataValidationError("OHLC violation: high < max(open, close).")
        if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
            raise DataValidationError("OHLC violation: low > min(open, close).")
        if (frame["volume"] < 0).any():
            raise DataValidationError("OHLCV violation: negative volume.")


def load_m15_ohlcv(csv_path: str) -> pd.DataFrame:
    """
    [PURPOSE]: Retain a deprecated compatibility adapter backed by strict validation.
    [DEPENDENCIES]: DatasetLoader validation primitives, Timeframe.
    [ARGS]: csv_path — M15 CSV path.
    [RETURNS]: Canonical validated M15 DataFrame.
    [SIDE EFFECTS]: Reads storage and raises DataValidationError for invalid data.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise DataValidationError(f"Dataset storage not found: {path}")
    frame = canonicalize_ohlcv(pd.read_csv(path))
    timestamps = frame["timestamp"]
    if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise DataValidationError("Timestamps must be unique and strictly increasing.")
    DatasetLoader._validate_ohlcv_bounds(frame)
    interval = pd.Timedelta(seconds=Timeframe.M15.to_seconds())
    if (timestamps.diff().dropna() != interval).any():
        raise DataValidationError("M15 dataset contains missing or irregular candles.")
    return frame
