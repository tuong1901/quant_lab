"""
[PURPOSE]: Modular Building Blocks (Indicators, Zone Filters, Entry Signals).
[DEPENDENCIES]: None.
"""

from typing import Dict, Callable

ENTRY_RULES: Dict[str, Callable] = {}
EXIT_RULES: Dict[str, Callable] = {}
