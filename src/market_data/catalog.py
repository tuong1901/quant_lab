"""
Dataset Catalog Registry (`src/market_data/catalog.py`).

Centralized registry for managing and retrieving historical Market Datasets.
"""

from typing import Dict, List, Optional
import os

from src.market_data.exceptions import DatasetNotFoundError, DuplicateDatasetError, CatalogError
from src.market_data.dataset import Dataset


class DatasetCatalog:
    """
    [PURPOSE]: Registry storing and providing lookup for immutable Dataset instances.
    [DEPENDENCIES]: Uses Dataset, DatasetNotFoundError, DuplicateDatasetError.
    [ARGS]: None.
    [RETURNS]: DatasetCatalog instance.
    [SIDE EFFECTS]: Maintains internal registry dictionary.
    """

    def __init__(self) -> None:
        """
        [PURPOSE]: Initialize an empty DatasetCatalog registry.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes internal dict self._datasets.
        """
        # Internal dictionary mapping identity string ("dataset_id:v{version}") -> Dataset instance
        self._datasets: Dict[str, Dataset] = {}

    def register(self, dataset: Dataset) -> None:
        """
        [PURPOSE]: Register a new immutable Dataset in the catalog.
        [DEPENDENCIES]: Calls dataset.identity.
        [ARGS]: dataset — Immutable Dataset object.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates internal catalog registry (adds dataset key).
        """
        if not isinstance(dataset, Dataset):
            raise CatalogError(f"Expected Dataset instance, got {type(dataset)}")

        identity = dataset.identity
        if identity in self._datasets:
            raise DuplicateDatasetError(f"Dataset '{identity}' is already registered in the catalog.")

        self._datasets[identity] = dataset

    def get(self, dataset_id: str, version: int) -> Dataset:
        """
        [PURPOSE]: Retrieve a registered Dataset by dataset_id and version.
        [DEPENDENCIES]: Raises DatasetNotFoundError if key does not exist.
        [ARGS]:
            dataset_id — Dataset string identifier (e.g. 'btcusdt_binance_perp_15m').
            version — Version integer (e.g. 3).
        [RETURNS]: Dataset instance.
        [SIDE EFFECTS]: None (pure lookup).
        """
        if not dataset_id or not isinstance(dataset_id, str):
            raise CatalogError("dataset_id must be a non-empty string.")

        identity = f"{dataset_id.strip()}:v{version}"
        if identity not in self._datasets:
            raise DatasetNotFoundError(
                f"Dataset identity '{identity}' not found in catalog. Available identities: {list(self._datasets.keys())}"
            )

        return self._datasets[identity]

    def exists(self, dataset_id: str, version: int) -> bool:
        """
        [PURPOSE]: Check whether a specific dataset_id and version exists in the catalog.
        [DEPENDENCIES]: None.
        [ARGS]:
            dataset_id — Dataset string identifier.
            version — Version integer.
        [RETURNS]: bool True if registered, False otherwise.
        [SIDE EFFECTS]: None.
        """
        if not dataset_id or not isinstance(dataset_id, str):
            return False
        identity = f"{dataset_id.strip()}:v{version}"
        return identity in self._datasets

    def list(self) -> List[Dataset]:
        """
        [PURPOSE]: List all registered Dataset instances in the catalog.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: List of Dataset objects.
        [SIDE EFFECTS]: None.
        """
        return list(self._datasets.values())

    def list_versions(self, dataset_id: str) -> List[int]:
        """
        [PURPOSE]: List all available versions for a given dataset_id in ascending order.
        [DEPENDENCIES]: Filters internal datasets.
        [ARGS]: dataset_id — Dataset string identifier.
        [RETURNS]: List of integer versions (e.g. [1, 2, 3]).
        [SIDE EFFECTS]: None.
        """
        if not dataset_id or not isinstance(dataset_id, str):
            return []

        target_id = dataset_id.strip()
        versions = []
        for ds in self._datasets.values():
            if ds.dataset_id == target_id:
                versions.append(ds.version)

        return sorted(versions)
