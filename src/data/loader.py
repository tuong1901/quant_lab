"""
Dataset Loader & Validator (`src/data/loader.py`).
"""

from dataclasses import dataclass
from datetime import timezone
import os
import pandas as pd

from src.data.exceptions import DataValidationError, InvalidDatasetError
from src.data.dataset import Dataset
from src.data.versioning import calculate_content_hash


@dataclass(frozen=True)
class MarketData:
    """
    [PURPOSE]: Container holding loaded DataFrame along with its immutable Dataset metadata.
    """
    dataset: Dataset
    df: pd.DataFrame


class DatasetLoader:
    """
    [PURPOSE]: Service responsible for reading dataset files and performing strict validation.
    """

    def load(self, dataset: Dataset) -> MarketData:
        """[PURPOSE]: Load and validate OHLCV dataset from physical storage."""
        if not isinstance(dataset, Dataset):
            raise InvalidDatasetError(f"Expected Dataset instance, got {type(dataset)}")

        file_path = dataset.storage_reference.path
        if not os.path.exists(file_path):
            raise DataValidationError(f"Storage reference file not found at path: {file_path}")

        df = self._read_file(file_path)
        self._validate_schema(df)
        df = self._validate_and_format_timestamps(df, dataset)
        self._validate_ohlcv_bounds(df)

        computed_hash = calculate_content_hash(df)
        if computed_hash.lower() != dataset.content_hash.lower():
            raise DataValidationError(
                f"Content hash mismatch for dataset '{dataset.identity}'. "
                f"Expected: {dataset.content_hash}, Computed: {computed_hash}"
            )

        missing_count = self.detect_missing_candles(df, dataset.timeframe)
        if missing_count > 0:
            pass

        return MarketData(dataset=dataset, df=df)

    def _read_file(self, file_path: str) -> pd.DataFrame:
        lower_path = file_path.lower()
        try:
            if lower_path.endswith(".parquet") or lower_path.endswith(".pq"):
                return pd.read_parquet(file_path)
            elif lower_path.endswith(".csv"):
                return pd.read_csv(file_path)
            else:
                try:
                    return pd.read_parquet(file_path)
                except Exception:
                    return pd.read_csv(file_path)
        except Exception as e:
            raise DataValidationError(f"Failed to read file from '{file_path}': {str(e)}")

    def _validate_schema(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise DataValidationError("Loaded dataset DataFrame is empty.")

        required_cols = {"open", "high", "low", "close", "volume"}
        cols = {c.lower() for c in df.columns}
        missing = required_cols - cols
        if missing:
            raise DataValidationError(f"Dataset missing required OHLCV columns: {missing}")

        has_timestamp_col = "timestamp" in cols or "time" in cols or "date" in cols
        has_timestamp_idx = isinstance(df.index, pd.DatetimeIndex) or df.index.name == "timestamp"
        if not (has_timestamp_col or has_timestamp_idx):
            raise DataValidationError("Dataset must contain a 'timestamp' column or DatetimeIndex.")

    def _validate_and_format_timestamps(self, df: pd.DataFrame, dataset: Dataset) -> pd.DataFrame:
        working_df = df.copy()

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

        parsed_ts = pd.to_datetime(ts_series, utc=True)
        working_df["timestamp"] = parsed_ts

        if parsed_ts.isna().any():
            raise DataValidationError("Found invalid or unparseable NaT timestamps in dataset.")

        if parsed_ts.duplicated().any():
            dup_sample = parsed_ts[parsed_ts.duplicated()].iloc[0]
            raise DataValidationError(f"Duplicate timestamp detected in dataset: {dup_sample}")

        if not parsed_ts.is_monotonic_increasing:
            raise DataValidationError("Timestamps are not strictly monotonic increasing.")

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
        open_s = df["open"]
        high_s = df["high"]
        low_s = df["low"]
        close_s = df["close"]
        volume_s = df["volume"]

        if (high_s < low_s).any():
            invalid_rows = df[high_s < low_s]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: high < low at timestamp {bad_ts}")

        max_body = open_s.combine(close_s, max)
        if (high_s < max_body).any():
            invalid_rows = df[high_s < max_body]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: high < max(open, close) at timestamp {bad_ts}")

        min_body = open_s.combine(close_s, min)
        if (low_s > min_body).any():
            invalid_rows = df[low_s > min_body]
            bad_ts = invalid_rows["timestamp"].iloc[0] if "timestamp" in invalid_rows else "unknown"
            raise DataValidationError(f"OHLC violation: low > min(open, close) at timestamp {bad_ts}")

        if (volume_s < 0).any():
            raise DataValidationError("OHLCV violation: negative volume detected.")

    def detect_missing_candles(self, df: pd.DataFrame, timeframe: Any) -> int:
        if df.empty or len(df) < 2:
            return 0

        tf_seconds = pd.Timedelta(seconds=timeframe.to_seconds())
        ts_diff = df["timestamp"].diff().dropna()

        gaps = ts_diff[ts_diff > tf_seconds]
        missing_bars = 0
        for gap in gaps:
            missing_bars += int(gap / tf_seconds) - 1

        return missing_bars


def load_m15_ohlcv(csv_path: str) -> pd.DataFrame:
    """
    [PURPOSE]: Load M15 OHLCV dataset from CSV into a clean pandas DataFrame.
    """
    df = pd.read_csv(csv_path)
    col_map = {col: col.lower().strip() for col in df.columns}
    df = df.rename(columns=col_map)
    
    required_cols = ['open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' missing from dataset {csv_path}")
            
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    if 'volume' in df.columns:
        df['volume'] = df['volume'].astype(float)
    else:
        df['volume'] = 1.0
        
    return df
