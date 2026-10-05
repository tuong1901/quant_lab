"""
Dataset Catalog Registry Container (`src/data/catalog.py`).
"""

import os
from typing import Dict, List, Optional
from src.data.dataset import Dataset
from src.data.exceptions import DuplicateDatasetError, DatasetNotFoundError


class DatasetCatalog:
    """
    [PURPOSE]: Registry for managing, querying, and loading Dataset definitions.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Dataset] = {}

    def register(self, dataset: Dataset) -> None:
        """[PURPOSE]: Register a Dataset definition entity in catalog."""
        identity = dataset.identity
        if identity in self._registry:
            raise DuplicateDatasetError(f"Dataset identity '{identity}' already registered in catalog.")
        self._registry[identity] = dataset

    def get(self, identity: str) -> Dataset:
        """[PURPOSE]: Retrieve Dataset definition by canonical identity string."""
        if identity not in self._registry:
            # Fallback search by dataset_id if version omitted
            matches = [ds for ds in self._registry.values() if ds.dataset_id == identity]
            if len(matches) == 1:
                return matches[0]
            raise DatasetNotFoundError(f"Dataset '{identity}' not found in catalog.")
        return self._registry[identity]

    def exists(self, identity: str) -> bool:
        """[PURPOSE]: Check if Dataset identity exists in catalog."""
        return identity in self._registry or any(ds.dataset_id == identity for ds in self._registry.values())

    def list(self) -> List[Dataset]:
        """[PURPOSE]: List all registered Datasets."""
        return list(self._registry.values())

    def list_versions(self, dataset_id: str) -> List[str]:
        """
        [PURPOSE]: List registered versions for one dataset identifier in ascending order.
        [DEPENDENCIES]: Internal Dataset registry.
        [ARGS]: dataset_id — Dataset identifier without version suffix.
        [RETURNS]: Sorted list of version strings.
        [SIDE EFFECTS]: None.
        """
        return sorted(ds.version for ds in self._registry.values() if ds.dataset_id == dataset_id)

    def load_from_file(self, yaml_path: str) -> Dataset:
        """[PURPOSE]: Load dataset definition from YAML file and register it."""
        ds = Dataset.from_yaml(yaml_path)
        self.register(ds)
        return ds

    def load_from_dir(self, dir_path: str) -> List[Dataset]:
        """[PURPOSE]: Load all dataset definition YAML files from directory."""
        loaded = []
        if not os.path.exists(dir_path):
            return loaded

        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    full_p = os.path.join(root, f)
                    ds = self.load_from_file(full_p)
                    loaded.append(ds)
        return loaded
