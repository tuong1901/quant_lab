"""
Dataset Content Hash & Versioning Engine (`src/data/versioning.py`).
"""

import hashlib
import pandas as pd
from src.data.exceptions import DataValidationError


def calculate_content_hash(df: pd.DataFrame) -> str:
    """
    [PURPOSE]: Compute SHA-256 content hash of DataFrame for deterministic versioning.
    """
    if df.empty:
        raise DataValidationError("Cannot calculate content hash for an empty DataFrame.")

    cols_to_hash = [c for c in ["timestamp", "open", "high", "low", "close", "volume"] if c in df.columns]

    hasher = hashlib.sha256()
    for col in cols_to_hash:
        hasher.update(col.encode("utf-8"))
        ser = df[col]
        if pd.api.types.is_datetime64_any_dtype(ser):
            buf = ser.astype("int64").to_numpy().tobytes()
        else:
            buf = ser.to_numpy().tobytes()
        hasher.update(buf)

    return hasher.hexdigest()


def verify_dataset_hash(df: pd.DataFrame, expected_hash: str) -> bool:
    """
    [PURPOSE]: Verify that computed DataFrame content hash matches expected SHA-256 hash.
    """
    computed = calculate_content_hash(df)
    return computed.lower() == expected_hash.lower()
