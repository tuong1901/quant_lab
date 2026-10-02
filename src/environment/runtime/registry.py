"""
Registry component for dynamic services and dependency lookup in Environment.
"""

from typing import Any, Dict
from src.environment.exceptions import EnvironmentConstructionError, MissingDependencyError


class Registry:
    """
    [PURPOSE]: Maintain an isolated key-value store for optional or custom dynamic runtime dependencies.
    [DEPENDENCIES]: Uses EnvironmentConstructionError and MissingDependencyError from src.environment.exceptions.
    [ARGS]: None upon initialization.
    [RETURNS]: Registry instance.
    [SIDE EFFECTS]: Stores dependencies in memory.
    """

    def __init__(self) -> None:
        """
        [PURPOSE]: Initialize an empty registry storage map.
        [DEPENDENCIES]: None.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes private dictionary _storage.
        """
        self._storage: Dict[str, Any] = {}

    def register(self, key: str, val: Any) -> None:
        """
        [PURPOSE]: Register a dynamic dependency under a unique key.
        [DEPENDENCIES]: Raises EnvironmentConstructionError if key is already registered.
        [ARGS]: key — Unique string identifier; val — Dependency instance or object.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates internal registry dictionary.
        """
        if key in self._storage:
            raise EnvironmentConstructionError(f"Duplicate registry key detected: '{key}'")
        self._storage[key] = val

    def get(self, key: str, default: Any = None) -> Any:
        """
        [PURPOSE]: Retrieve a registered dependency by key, returning default if not found.
        [DEPENDENCIES]: None.
        [ARGS]: key — Dependency key; default — Fallback return value (default None).
        [RETURNS]: Registered value if key exists, else default.
        [SIDE EFFECTS]: None (pure lookup).
        """
        return self._storage.get(key, default)

    def contains(self, key: str) -> bool:
        """
        [PURPOSE]: Check whether a dependency key exists in the registry.
        [DEPENDENCIES]: None.
        [ARGS]: key — String key to check.
        [RETURNS]: bool — True if key exists, False otherwise.
        [SIDE EFFECTS]: None.
        """
        return key in self._storage

    def require(self, key: str) -> Any:
        """
        [PURPOSE]: Retrieve a required dependency by key, raising an error if missing.
        [DEPENDENCIES]: Raises MissingDependencyError if key does not exist.
        [ARGS]: key — Required dependency key string.
        [RETURNS]: Any — Registered dependency value.
        [SIDE EFFECTS]: None.
        """
        if key not in self._storage:
            raise MissingDependencyError(f"Required registry key '{key}' was not found.")
        return self._storage[key]
