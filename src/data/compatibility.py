"""
Dataset Compatibility Validator (`src/data/compatibility.py`).
"""

from src.data.dataset import Dataset
from src.data.exceptions import IncompatibleDatasetError


def validate_compatible_datasets(strategy_ds: Dataset, execution_ds: Dataset) -> None:
    """
    [PURPOSE]: Ensure Strategy Dataset and Execution Dataset share compatible Market and Timeframe specifications.
    """
    if strategy_ds.market.identity != execution_ds.market.identity:
        raise IncompatibleDatasetError(
            f"Market mismatch: Strategy dataset market '{strategy_ds.market.identity}' "
            f"does not match Execution dataset market '{execution_ds.market.identity}'."
        )

    if execution_ds.timeframe.to_seconds() > strategy_ds.timeframe.to_seconds():
        raise IncompatibleDatasetError(
            f"Execution timeframe '{execution_ds.timeframe.value}' cannot be higher "
            f"than Strategy timeframe '{strategy_ds.timeframe.value}'."
        )

    overlap_start = max(strategy_ds.data_range.start, execution_ds.data_range.start)
    overlap_end = min(strategy_ds.data_range.end, execution_ds.data_range.end)
    if overlap_start >= overlap_end:
        raise IncompatibleDatasetError(
            "Strategy and execution datasets must have an overlapping DataRange."
        )
