"""
Dataset Compatibility Validation Engine (`src/market_data/compatibility.py`).

Validates compatibility between Strategy Datasets and LTF Execution Datasets.
"""

from src.market_data.dataset import Dataset
from src.market_data.exceptions import IncompatibleDatasetError


def validate_compatible_datasets(strategy_dataset: Dataset, execution_dataset: Dataset) -> bool:
    """
    [PURPOSE]: Ensure Strategy Dataset and Execution Dataset belong to the same market and have overlapping date ranges.
    [DEPENDENCIES]: Uses Dataset, raises IncompatibleDatasetError.
    [ARGS]:
        strategy_dataset — Dataset instance used for strategy signal generation.
        execution_dataset — Dataset instance used for execution fill simulation (e.g. M1 LTF replay).
    [RETURNS]: bool True if datasets are compatible.
    [SIDE EFFECTS]: None (pure validation).
    """
    if not isinstance(strategy_dataset, Dataset) or not isinstance(execution_dataset, Dataset):
        raise IncompatibleDatasetError("Both strategy_dataset and execution_dataset must be Dataset instances.")

    m_strat = strategy_dataset.market
    m_exec = execution_dataset.market

    # 1. Validate Market identity attributes match
    if m_strat.venue != m_exec.venue:
        raise IncompatibleDatasetError(
            f"Venue mismatch between strategy dataset ('{m_strat.venue}') and execution dataset ('{m_exec.venue}')."
        )

    if m_strat.symbol != m_exec.symbol:
        raise IncompatibleDatasetError(
            f"Symbol mismatch between strategy dataset ('{m_strat.symbol}') and execution dataset ('{m_exec.symbol}')."
        )

    if m_strat.market_type != m_exec.market_type:
        raise IncompatibleDatasetError(
            f"Market type mismatch between strategy dataset ('{m_strat.market_type}') and execution dataset ('{m_exec.market_type}')."
        )

    if m_strat.quote_currency != m_exec.quote_currency:
        raise IncompatibleDatasetError(
            f"Quote currency mismatch between strategy dataset ('{m_strat.quote_currency}') and execution dataset ('{m_exec.quote_currency}')."
        )

    # 2. Validate Data Range overlap
    start_overlap = max(strategy_dataset.data_range.start, execution_dataset.data_range.start)
    end_overlap = min(strategy_dataset.data_range.end, execution_dataset.data_range.end)

    if start_overlap >= end_overlap:
        raise IncompatibleDatasetError(
            f"No date range overlap between strategy dataset ({strategy_dataset.data_range.start} to {strategy_dataset.data_range.end}) "
            f"and execution dataset ({execution_dataset.data_range.start} to {execution_dataset.data_range.end})."
        )

    return True
