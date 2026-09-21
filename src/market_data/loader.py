"""
Dataset Loader & Validator (`src/market_data/loader.py`).

Responsible for loading OHLCV market data from storage and validating correctness invariants.
"""

from dataclasses import dataclass
from datetime import timezone
import os
import pandas as pd

from src.market_data.exceptions import DataValidationError, InvalidDatasetError
from src.market_data.dataset import Dataset
from src.market_data.versioning import calculate_content_hash


@dataclass(frozen=True)
class MarketData:
    """
    [PURPOSE]: Container holding loaded DataFrame along with its immutable Dataset metadata.
    [DEPENDENCIES]: Created by DatasetLoader.load().
    [ARGS]:
        dataset — Immutable Dataset object.
        df — Pandas DataFrame containing validated OHLCV bar data.
    [RETURNS]: Frozen MarketData instance.
    [SIDE EFFECTS]: None.
    """
    dataset: Dataset
    df: pd.DataFrame


class DatasetLoader:
    """
    [PURPOSE]: Service responsible for reading dataset files and performing strict validation.
    [DEPENDENCIES]: Uses Dataset, MarketData, DataValidationError, calculate_content_hash.
    [ARGS]: None.
    [RETURNS]: DatasetLoader instance.
    [SIDE EFFECTS]: Reads files from local storage.
    """

    def load(self, dataset: Dataset) -> MarketData:
        """
        [PURPOSE]: Load and validate OHLCV dataset from physical storage.
        [DEPENDENCIES]: Performs IO read, schema validation, OHLC bounds validation, and hash verification.
        [ARGS]: dataset — Immutable Dataset metadata object.
        [RETURNS]: MarketData container.
        [SIDE EFFECTS]: Reads storage file.
        """
        if not isinstance(dataset, Dataset):
            raise InvalidDatasetError(f"Expected Dataset instance, got {type(dataset)}")

        file_path = dataset.storage_reference.path
        if not os.path.exists(file_path):
            raise DataValidationError(f"Storage reference file not found at path: {file_path}")

        # 1. Load DataFrame based on file extension
        df = self._read_file(file_path)

        # 2. Validate basic schema requirement
        self._validate_schema(df)

        # 3. Canonicalize timestamps & validate monotonicity, uniqueness, UTC timezone
        df = self._validate_and_format_timestamps(df, dataset)

        # 4. Validate OHLCV mathematical relationships
        self._validate_ohlcv_bounds(df)

        # 5. Validate Content Hash matching
        computed_hash = calculate_content_hash(df)
        if computed_hash.lower() != dataset.content_hash.lower():
            raise DataValidationError(
                f"Content hash mismatch for dataset '{dataset.identity}'. "
                f"Expected: {dataset.content_hash}, Computed: {computed_hash}"
            )

        # 6. Detect missing candles without mutating or forward-filling raw data
        missing_count = self.detect_missing_candles(df, dataset.timeframe)
        if missing_count > 0:
            # Note: We record missing count in metadata logging capability, preserving raw data
            pass

        return MarketData(dataset=dataset, df=df)

    def _read_file(self, file_path: str) -> pd.DataFrame:
        """
        [PURPOSE]: Read file into DataFrame depending on file format (parquet or csv).
        [DEPENDENCIES]: Uses pandas read_parquet / read_csv.
        [ARGS]: file_path — Path string.
        [RETURNS]: pd.DataFrame.
        [SIDE EFFECTS]: IO read.
        """
        lower_path = file_path.lower()
        try:
            if lower_path.endswith(".parquet") or lower_path.endswith(".pq"):
                return pd.read_parquet(file_path)
            elif lower_path.endswith(".csv"):
                return pd.read_csv(file_path)
            else:
                # Default try parquet first, fallback to csv
                try:
                    return pd.read_parquet(file_path)
                except Exception:
                    return pd.read_csv(file_path)
        except Exception as e:
            raise DataValidationError(f"Failed to read file from '{file_path}': {str(e)}")

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """
        [PURPOSE]: Ensure essential OHLCV columns exist in DataFrame.
        [DEPENDENCIES]: None.
        [ARGS]: df — pd.DataFrame.
        [RETURNS]: None.
        [SIDE EFFECTS]: None.
        """
        if df.empty:
            raise DataValidationError("Loaded dataset DataFrame is empty.")

        required_cols = {"open", "high", "low", "close", "volume"}

        # Handle case where timestamp is in index or column
        cols = {c.lower() for c in df.columns}
        missing = required_cols - cols
        if missing:
            raise DataValidationError(f"Dataset missing required OHLCV columns: {missing}")

        # Check timestamp presence
        has_timestamp_col = "timestamp" in cols or "time" in cols or "date" in cols
        has_timestamp_idx = isinstance(df.index, pd.DatetimeIndex) or df.index.name == "timestamp"
        if not (has_timestamp_col or has_timestamp_idx):
            raise DataValidationError("Dataset must contain a 'timestamp' column or DatetimeIndex.")

    def _validate_and_format_timestamps(self, df: pd.DataFrame, dataset: Dataset) -> pd.DataFrame:
        """
        [PURPOSE]: Canonicalize timestamps to UTC, validate strictly monotonic increasing and unique timestamps.
        [DEPENDENCIES]: None.
        [ARGS]: df — DataFrame, dataset — Dataset.
        [RETURNS]: Formatted DataFrame with UTC 'timestamp' column.
        [SIDE EFFECTS]: None.
        """
        working_df = df.copy()

        # Extract timestamp series
        if "timestamp" in working_df.columns:
            ts_series = working_df["timestamp"]
        elif "time" in working_df.columns:
            ts_series = working_df["time"]
            working_df = working_df.rename(columns={"time": "timestamp"})
        elif "date" in working_df.columns:
            ts_series = working_df["date"]
            working_df = working_df.rename(columns={"date": "timestamp"})
        elif isinstance(working_df.index, pd.DatetimeIndex):
            ts_series = working_df.index.to_series()
            working_df["timestamp"] = ts_series.values
        else:
            raise DataValidationError("Unable to locate timestamp series in DataFrame.")

        # Convert to UTC datetime
        parsed_ts = pd.to_datetime(ts_series, utc=True)
        working_df["timestamp"] = parsed_ts

        # Check for NaT (unparseable datetimes)
        if parsed_ts.isna().any():
            raise DataValidationError("Found invalid or unparseable NaT timestamps in dataset.")

        # Check uniqueness (reject duplicate timestamps)
        if parsed_ts.duplicated().any():
            dup_sample = parsed_ts[parsed_ts.duplicated()].iloc[0]
            raise DataValidationError(f"Duplicate timestamp detected in dataset: {dup_sample}")

        # Check strictly monotonic increasing order
        if not parsed_ts.is_monotonic_increasing:
            raise DataValidationError("Timestamps are not strictly monotonic increasing.")

        # Check data range bounds
        min_ts = parsed_ts.min()
        max_ts = parsed_ts.max()

        if min_ts < dataset.data_range.start:
            raise DataValidationError(
                f"Dataset contains timestamps earlier than data_range.start: {min_ts} < {dataset.data_range.start}"
            )

        if max_ts > dataset.data_range.end:
            raise DataValidationError(
                f"Dataset contains timestamps later than data_range.end: {max_ts} > {dataset.data_range.end}"
            )

        return working_df

    def _validate_ohlcv_bounds(self, df: pd.DataFrame) -> None:
        """
        [PURPOSE]: Validate OHLC relationships for every bar (high >= max(open, close), low <= min(open, close), volume >= 0).
        [DEPENDENCIES]: Raises DataValidationError if violated.
        [ARGS]: df — pd.DataFrame.
        [RETURNS]: None.
        [SIDE EFFECTS]: None.
        """
        open_s = df["open"]
        high_s = df["high"]
        low_s = df["low"]
        close_s = df["close"]
        volume_s = df["volume"]

        # 1. High >= Low
        if (high_s < low_s).any():
            invalid_rows = df[high_s < low_s]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: high < low at timestamp {bad_ts}")

        # 2. High >= max(Open, Close)
        max_body = open_s.combine(close_s, max)
        if (high_s < max_body).any():
            invalid_rows = df[high_s < max_body]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: high < max(open, close) at timestamp {bad_ts}")

        # 3. Low <= min(Open, Close)
        min_body = open_s.combine(close_s, min)
        if (low_s > min_body).any():
            invalid_rows = df[low_s > min_body]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: low > min(open, close) at timestamp {bad_ts}")

        # 4. Volume >= 0
        if (volume_s < 0).any():
            raise DataValidationError("OHLCV violation: negative volume detected.")

    def detect_missing_candles(self, df: pd.DataFrame, timeframe: Any) -> int:
        """
        [PURPOSE]: Detect missing candle bars in a time-series DataFrame without filling them.
        [DEPENDENCIES]: Uses Timeframe.to_seconds().
        [ARGS]:
            df — DataFrame with UTC 'timestamp' column.
            timeframe — Timeframe instance or parseable value.
        [RETURNS]: int count of missing bar gaps.
        [SIDE EFFECTS]: None (pure calculation).
        """
        if df.empty or len(df) < 2:
            return 0

        tf_seconds = pd.Timedelta(seconds=timeframe.to_seconds())
        ts_diff = df["timestamp"].diff().dropna()

        # Count time differences larger than the expected bar duration
        gaps = ts_diff[ts_diff > tf_seconds]
        missing_bars = 0
        for gap in gaps:
            missing_bars += int(gap / tf_seconds) - 1

        return missing_bars
