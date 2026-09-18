"""
Dataset Versioning & Content Hashing Engine (`src/market_data/versioning.py`).

Provides deterministic fingerprint computation for market datasets.
"""

import hashlib
import pandas as pd

from src.market_data.exceptions import DataValidationError


def calculate_content_hash(df: pd.DataFrame) -> str:
    """
    [PURPOSE]: Compute a 100% deterministic SHA-256 fingerprint from a market data DataFrame.
    [DEPENDENCIES]: Used by DatasetLoader and Dataset versioning tools.
    [ARGS]: df — Pandas DataFrame containing OHLCV bar data.
    [RETURNS]: str 64-character SHA-256 hex digest.
    [SIDE EFFECTS]: Pure function (does not mutate input DataFrame).
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise DataValidationError("Cannot compute content hash for empty or None DataFrame.")

    # 1. Create a copy to avoid mutating original DataFrame
    working_df = df.copy()

    # 2. Handle timestamp index or column canonicalization
    if "timestamp" in working_df.columns:
        working_df["timestamp"] = pd.to_datetime(working_df["timestamp"], utc=True)
        working_df = working_df.sort_values(by="timestamp").reset_index(drop=True)
        # Format timestamps as canonical UTC ISO strings
        working_df["timestamp"] = working_df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(working_df.index, pd.DatetimeIndex):
        working_df.index = pd.to_datetime(working_df.index, utc=True)
        working_df = working_df.sort_index()
        working_df["timestamp"] = working_df.index.strftime("%Y-%m-%dT%H:%M:%SZ")
        working_df = working_df.reset_index(drop=True)

    # 3. Sort columns alphabetically to ensure column order independence
    sorted_cols = sorted(working_df.columns)
    working_df = working_df[sorted_cols]

    # 4. Canonicalize string representation of data values
    # Format floating numbers with fixed precision (6 decimal places) to avoid platform float serialization noise
    canonical_rows = []
    for row in working_df.itertuples(index=False):
        formatted_fields = []
        for val in row:
            if isinstance(val, float):
                formatted_fields.append(f"{val:.6f}")
            else:
                formatted_fields.append(str(val))
        canonical_rows.append(",".join(formatted_fields))

    canonical_text = "\n".join(canonical_rows)
    hash_digest = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    return hash_digest


def verify_dataset_hash(df: pd.DataFrame, expected_hash: str) -> bool:
    """
    [PURPOSE]: Verify whether a DataFrame's computed content hash matches the expected hash.
    [DEPENDENCIES]: Calls calculate_content_hash.
    [ARGS]:
        df — Market data DataFrame.
        expected_hash — Expected SHA-256 string digest.
    [RETURNS]: bool True if hash matches, False otherwise.
    [SIDE EFFECTS]: None.
    """
    if not expected_hash or not isinstance(expected_hash, str):
        return False
    actual_hash = calculate_content_hash(df)
    return actual_hash.lower().strip() == expected_hash.lower().strip()
