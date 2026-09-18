"""
[PURPOSE]: Dataclass representing portfolio state summary.
[DEPENDENCIES]: core.positions.
"""

from dataclasses import dataclass, field
from typing import Dict
from src.core.positions import Position

@dataclass
class PortfolioState:
    equity: float
    cash: float
    margin_used: float
    positions: Dict[str, Position] = field(default_factory=dict)
