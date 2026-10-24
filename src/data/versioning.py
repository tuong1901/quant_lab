"""Canonical content fingerprinting for strict OHLCV datasets."""

import hashlib
import json
import logging

import numpy as np
import pandas as pd

from src.data.exceptions import DataValidationError
from src.data.columns import CANONICAL_COLUMNS, ColumnPolicy

logger = logging.getLogger(__name__)


def enforce_open_close_continuity(frame: pd.DataFrame, dataset_identity: str = "<direct>") -> pd.DataFrame:
    """
    [PURPOSE]: Align every non-initial candle open with the preceding close and repair only invalid direction-specific wicks.
    [DEPENDENCIES]: pandas.
    [ARGS]: frame — Canonical OHLCV in source order; dataset_identity — diagnostic label.
    [RETURNS]: Copy whose corrected candles preserve continuity and valid OHLC bounds.
    [SIDE EFFECTS]: Emits WARNING per repair and INFO totals; rejects invalid corrected OHLCV.
    """
    if frame.empty or frame.columns.has_duplicates or set(CANONICAL_COLUMNS) - set(frame.columns):
        raise DataValidationError("Continuity repair requires non-empty canonical OHLCV with unique columns.")
    if frame.loc[:, CANONICAL_COLUMNS].isna().any().any():
        raise DataValidationError("Continuity repair requires non-null OHLCV.")
    numeric = frame.loc[:, CANONICAL_COLUMNS[1:]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise DataValidationError("Continuity repair requires finite OHLCV.")
    cleaned = frame.copy().reset_index(drop=True)
    open_count = high_count = low_count = 0
    if len(cleaned) > 1:
        candidate_index = cleaned.index[1:]
        original_opens = cleaned.loc[candidate_index, "open"].to_numpy(copy=True)
        previous_closes = cleaned["close"].iloc[:-1].to_numpy()
        highs = cleaned.loc[candidate_index, "high"].to_numpy(copy=True)
        lows = cleaned.loc[candidate_index, "low"].to_numpy(copy=True)
        closes = cleaned.loc[candidate_index, "close"].to_numpy()
        original_highs, original_lows = highs.copy(), lows.copy()
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
        for offset in np.flatnonzero(discontinuous):
            position = int(offset) + 1
            logger.warning(
                "candle_repaired dataset=%s row=%s timestamp=%s previous_close=%s "
                "open=%s->%s high=%s->%s low=%s->%s reason=open_close_discontinuity",
                dataset_identity, position, cleaned.at[position, "timestamp"], previous_closes[offset],
                original_opens[offset], corrected_opens[offset], original_highs[offset], highs[offset],
                original_lows[offset], lows[offset],
            )
        open_count, high_count, low_count = int(discontinuous.sum()), int(repair_high.sum()), int(repair_low.sum())
    logger.info("Repair summary dataset=%s rows=%s repaired_candles=%s open=%s high=%s low=%s",
                dataset_identity, len(cleaned), open_count, open_count, high_count, low_count)
    validate_ohlcv_bounds(cleaned)
    return cleaned


def validate_ohlcv_bounds(frame: pd.DataFrame) -> None:
    """
    [PURPOSE]: Reject invalid corrected OHLC ranges and negative volume.
    [DEPENDENCIES]: Continuity repair and DatasetLoader.
    [ARGS]: frame — finite numeric canonical OHLCV.
    [RETURNS]: None.
    [SIDE EFFECTS]: Raises DataValidationError on contract violations.
    """
    if (frame["high"] < frame["low"]).any():
        raise DataValidationError("OHLC violation: high < low.")
    if (frame["high"] < frame[["open", "close"]].max(axis=1)).any():
        raise DataValidationError("OHLC violation: high < max(open, close).")
    if (frame["low"] > frame[["open", "close"]].min(axis=1)).any():
        raise DataValidationError("OHLC violation: low > min(open, close).")
    if (frame["volume"] < 0).any():
        raise DataValidationError("OHLCV violation: negative volume.")


def canonicalize_ohlcv(frame: pd.DataFrame, columns: ColumnPolicy | None = None,
                       dataset_identity: str = "<direct>") -> pd.DataFrame:
    """
    [PURPOSE]: Apply explicit columns and enforce finite repaired OHLCV values.
    [DEPENDENCIES]: pandas, numpy, DataValidationError.
    [ARGS]: frame — raw input; columns — explicit policy or canonical-only; dataset_identity — log label.
    [RETURNS]: Canonical DataFrame with UTC timestamp and lowercase OHLCV columns.
    [SIDE EFFECTS]: Logs ignores/repairs; raises DataValidationError for invalid schema or values.
    """
    policy = columns if columns is not None else ColumnPolicy()
    result = policy.select(frame, dataset_identity)
    result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True, errors="coerce")
    for column in CANONICAL_COLUMNS[1:]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    canonical = result.loc[:, CANONICAL_COLUMNS]
    if canonical.isna().any().any() or not np.isfinite(canonical.loc[:, CANONICAL_COLUMNS[1:]].to_numpy(float)).all():
        raise DataValidationError("OHLCV values must be finite and non-null.")
    return enforce_open_close_continuity(result, dataset_identity)


def calculate_content_hash(frame: pd.DataFrame, columns: ColumnPolicy | None = None,
                           dataset_identity: str = "<direct>") -> str:
    """
    [PURPOSE]: Calculate a deterministic SHA-256 hash independent of input column order.
    [DEPENDENCIES]: canonicalize_ohlcv, hashlib, json.
    [ARGS]: frame — raw input; columns — explicit policy or canonical-only; dataset_identity — log label.
    [RETURNS]: Lowercase SHA-256 hexadecimal digest.
    [SIDE EFFECTS]: Emits repair warnings; raises DataValidationError for invalid data.
    """
    policy = columns if columns is not None else ColumnPolicy()
    canonical = canonicalize_ohlcv(frame, policy, dataset_identity)
    return _hash_canonical_frame(canonical, policy)


def _hash_canonical_frame(canonical: pd.DataFrame, policy: ColumnPolicy) -> str:
    """
    [PURPOSE]: Hash already validated output without reapplying mapping or logging duplicate repairs.
    [DEPENDENCIES]: DatasetLoader and calculate_content_hash; hashlib/json.
    [ARGS]: canonical — validated output; policy — feature schema used to produce it.
    [RETURNS]: SHA-256; old OHLCV v1 format or feature-aware v2 format.
    [SIDE EFFECTS]: None.
    """
    names = sorted(policy.features)
    header = b"ohlcv-v1|timestamp|open|high|low|close|volume\n"
    if names:
        schema = [(name, policy.features[name].type) for name in names]
        header = b"ohlcv-features-v2|" + json.dumps(schema, separators=(",", ":")).encode("utf-8") + b"\n"
    digest = hashlib.sha256(header)
    for timestamp, *values in canonical.loc[:, list(CANONICAL_COLUMNS) + names].itertuples(index=False, name=None):
        row = [
            timestamp.isoformat().replace("+00:00", "Z"),
            *[np.format_float_positional(float(value), unique=True, trim="-") for value in values],
        ]
        digest.update(json.dumps(row, separators=(",", ":")).encode("utf-8") + b"\n")
    return digest.hexdigest()


def verify_dataset_hash(frame: pd.DataFrame, expected_hash: str, columns: ColumnPolicy | None = None,
                        dataset_identity: str = "<direct>") -> bool:
    """
    [PURPOSE]: Compare canonical dataset content to one expected SHA-256 fingerprint.
    [DEPENDENCIES]: calculate_content_hash.
    [ARGS]: frame — input; expected_hash — digest; columns — policy; dataset_identity — log label.
    [RETURNS]: True when hashes match.
    [SIDE EFFECTS]: Emits repair warnings; raises DataValidationError when input data is invalid.
    """
    return calculate_content_hash(frame, columns, dataset_identity) == expected_hash.lower()
