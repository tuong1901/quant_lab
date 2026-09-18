"""
[PURPOSE]: Generic Component and Service Registry.
[DEPENDENCIES]: None.
"""

from typing import Dict, Any, Type

class Registry:
    """
    [PURPOSE]: Decorator-based registration for strategies and modules.
    [DEPENDENCIES]: None.
    """
    def __init__(self):
        self._registry: Dict[str, Type] = {}

    def register(self, name: str):
        def decorator(cls):
            self._registry[name] = cls
            return cls
        return decorator

    def get(self, name: str) -> Type:
        if name not in self._registry:
            raise KeyError(f"Component '{name}' not found in registry.")
        return self._registry[name]
