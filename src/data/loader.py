"""Strict physical loading and validation for market datasets."""

from dataclasses import dataclass
from pathlib import Path
import logging

import pandas as pd

from src.data.dataset import DataRange, Dataset
from src.data.exceptions import DataValidationError, InvalidDatasetError
from src.data.timeframe import Timeframe
from src.data.versioning import canonicalize_ohlcv, _hash_canonical_frame, validate_ohlcv_bounds
from src.data.columns import ColumnPolicy

logger = logging.getLogger(__name__)


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
        [PURPOSE]: Load a strict dataset with success and rejection diagnostics.
        [DEPENDENCIES]: _load_validated.
        [ARGS]: dataset — descriptor with explicit column policy.
        [RETURNS]: Verified MarketData.
        [SIDE EFFECTS]: Reads storage, logs summary/errors and propagates contract failures.
        """
        identity = getattr(dataset, "identity", "<invalid>")
        logger.info("Loading dataset=%s", identity)
        try:
            result = self._load_validated(dataset)
        except Exception:
            logger.exception("Dataset rejected identity=%s", identity)
            raise
        logger.info("Dataset loaded identity=%s rows=%s columns=%s hash_verified=True",
                    identity, len(result.df), list(result.df.columns))
        return result

    def _load_validated(self, dataset: Dataset) -> MarketData:
        """
        [PURPOSE]: Load a dataset and reject any schema, temporal, OHLCV, hash or gap breach.
        [DEPENDENCIES]: Dataset, canonicalize_ohlcv, _hash_canonical_frame.
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
        frame = canonicalize_ohlcv(raw, dataset.columns, dataset.identity)
        self._validate_temporal_contract(frame, dataset.data_range, dataset.timeframe)
        self._validate_ohlcv_bounds(frame)
        if _hash_canonical_frame(frame, dataset.columns) != dataset.content_hash:
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
        validate_ohlcv_bounds(frame)


def load_m15_ohlcv(csv_path: str, columns: ColumnPolicy | None = None) -> pd.DataFrame:
    """
    [PURPOSE]: Keep deprecated M15 loading explicit and auditable through the same policy.
    [DEPENDENCIES]: _load_m15_validated.
    [ARGS]: csv_path — CSV source; columns — explicit policy or canonical-only.
    [RETURNS]: Validated canonical M15 data.
    [SIDE EFFECTS]: Reads storage, logs warnings/errors, propagates validation failures.
    """
    logger.warning("Deprecated CSV adapter path=%s; descriptor/hash verification is unavailable", csv_path)
    try:
        frame = _load_m15_validated(csv_path, columns)
    except Exception:
        logger.exception("Legacy dataset rejected path=%s", csv_path)
        raise
    logger.info("Legacy dataset loaded path=%s rows=%s columns=%s", csv_path, len(frame), list(frame.columns))
    return frame


def _load_m15_validated(csv_path: str, columns: ColumnPolicy | None) -> pd.DataFrame:
    """
    [PURPOSE]: Retain a deprecated compatibility adapter backed by strict validation.
    [DEPENDENCIES]: DatasetLoader validation primitives, Timeframe.
    [ARGS]: csv_path — M15 CSV path; columns — explicit policy or canonical-only.
    [RETURNS]: Canonical validated M15 DataFrame.
    [SIDE EFFECTS]: Reads storage and raises DataValidationError for invalid data.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise DataValidationError(f"Dataset storage not found: {path}")
    frame = canonicalize_ohlcv(pd.read_csv(path), columns, str(path))
    timestamps = frame["timestamp"]
    if timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise DataValidationError("Timestamps must be unique and strictly increasing.")
    DatasetLoader._validate_ohlcv_bounds(frame)
    interval = pd.Timedelta(seconds=Timeframe.M15.to_seconds())
    if (timestamps.diff().dropna() != interval).any():
        raise DataValidationError("M15 dataset contains missing or irregular candles.")
    return frame
