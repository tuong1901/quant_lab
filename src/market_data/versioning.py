"""
[PURPOSE]: Hash verification and version control for datasets.
[DEPENDENCIES]: hashlib.
"""

import hashlib
import pandas as pd

def compute_dataset_hash(df: pd.DataFrame) -> str:
    """
    [PURPOSE]: Compute deterministic MD5 hash of market dataframe for versioning.
    [DEPENDENCIES]: hashlib.
    [ARGS]: df — DataFrame to hash.
    [RETURNS]: String MD5 hash.
    [SIDE EFFECTS]: None.
    """
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
