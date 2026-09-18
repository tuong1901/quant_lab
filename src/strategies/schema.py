"""
[PURPOSE]: Parameter Schema definition and validator for strategies.
[DEPENDENCIES]: None.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StrategySchema:
    name: str
    parameter_bounds: Dict[str, Any]
