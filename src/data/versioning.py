"""Canonical content fingerprinting for strict OHLCV datasets."""

import hashlib
import json

import numpy as np
import pandas as pd

from src.data.exceptions import DataValidationError

CANONICAL_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")


def enforce_open_close_continuity(frame: pd.DataFrame) -> pd.DataFrame:
    """
    [PURPOSE]: Align every non-initial candle open with the preceding close and repair only invalid direction-specific wicks.
    [DEPENDENCIES]: pandas.
    [ARGS]: frame — Canonical OHLCV DataFrame ordered by source row order.
    [RETURNS]: Copy whose corrected candles preserve continuity and valid OHLC bounds.
    [SIDE EFFECTS]: None; downstream OHLC validation rejects all unrelated invalid ranges.
    """
    cleaned = frame.copy()
    if len(cleaned) > 1:
        candidate_index = cleaned.index[1:]
        original_opens = cleaned.loc[candidate_index, "open"].to_numpy(copy=True)
        previous_closes = cleaned["close"].iloc[:-1].to_numpy()
        highs = cleaned.loc[candidate_index, "high"].to_numpy(copy=True)
        lows = cleaned.loc[candidate_index, "low"].to_numpy(copy=True)
        closes = cleaned.loc[candidate_index, "close"].to_numpy()
        discontinuous = original_opens != previous_closes

        corrected_opens = original_opens.copy()
        corrected_opens[discontinuous] = previous_closes[discontinuous]

        # Continuity sets open to the preceding close.  If that open becomes an
        # impossible wick extremum, repair the matching wick rather than undoing
        # continuity: green/flat candles need low <= open; red candles need high >= open.
        green_or_flat = closes >= corrected_opens
        repair_low = discontinuous & green_or_flat & (lows > corrected_opens)
        repair_high = discontinuous & ~green_or_flat & (highs < corrected_opens)
        lows[repair_low] = corrected_opens[repair_low]
        highs[repair_high] = corrected_opens[repair_high]
        cleaned.loc[candidate_index, "open"] = corrected_opens
        cleaned.loc[candidate_index, "high"] = highs
        cleaned.loc[candidate_index, "low"] = lows
    return cleaned


def canonicalize_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    """
    [PURPOSE]: Normalize aliases and enforce finite canonical OHLCV values.
    [DEPENDENCIES]: pandas, numpy, DataValidationError.
    [ARGS]: frame — Raw OHLCV DataFrame.
    [RETURNS]: Canonical DataFrame with UTC timestamp and lowercase OHLCV columns.
    [SIDE EFFECTS]: Raises DataValidationError for invalid schema or values.
    """
    aliases = {str(column).strip().lower(): column for column in frame.columns}
    timestamp_column = aliases.get("timestamp") or aliases.get("time") or aliases.get("date")
    required = {"open", "high", "low", "close", "volume"}
    if frame.empty or timestamp_column is None or required - set(aliases):
        raise DataValidationError("Dataset requires timestamp/time and open, high, low, close, volume.")
    result = frame.copy()
    result["timestamp"] = pd.to_datetime(result[timestamp_column], utc=True, errors="coerce")
    if timestamp_column != "timestamp":
        result = result.drop(columns=[timestamp_column])
    for column in required:
        result[column] = pd.to_numeric(result[aliases[column]], errors="coerce")
    canonical = result.loc[:, CANONICAL_COLUMNS]
    if canonical.isna().any().any() or not np.isfinite(canonical.loc[:, CANONICAL_COLUMNS[1:]].to_numpy(float)).all():
        raise DataValidationError("OHLCV values must be finite and non-null.")
    return enforce_open_close_continuity(result)


def calculate_content_hash(frame: pd.DataFrame) -> str:
    """
    [PURPOSE]: Calculate a deterministic SHA-256 hash independent of input column order.
    [DEPENDENCIES]: canonicalize_ohlcv, hashlib, json.
    [ARGS]: frame — Raw or canonical OHLCV DataFrame.
    [RETURNS]: Lowercase SHA-256 hexadecimal digest.
    [SIDE EFFECTS]: Raises DataValidationError for invalid data.
    """
    digest = hashlib.sha256(b"ohlcv-v1|timestamp|open|high|low|close|volume\n")
    canonical = canonicalize_ohlcv(frame)
    for timestamp, *values in canonical.loc[:, CANONICAL_COLUMNS].itertuples(index=False, name=None):
        row = [
            timestamp.isoformat().replace("+00:00", "Z"),
            *[np.format_float_positional(float(value), unique=True, trim="-") for value in values],
        ]
        digest.update(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
    return digest.hexdigest()


def verify_dataset_hash(frame: pd.DataFrame, expected_hash: str) -> bool:
    """
    [PURPOSE]: Compare canonical dataset content to one expected SHA-256 fingerprint.
    [DEPENDENCIES]: calculate_content_hash.
    [ARGS]: frame — OHLCV DataFrame; expected_hash — Expected lowercase or uppercase digest.
    [RETURNS]: True when hashes match.
    [SIDE EFFECTS]: Raises DataValidationError when input data is invalid.
    """
    return calculate_content_hash(frame) == expected_hash.lower()
