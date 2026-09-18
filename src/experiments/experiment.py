"""
[PURPOSE]: Experiment definition and container.
[DEPENDENCIES]: None.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ExperimentConfig:
    experiment_id: str
    strategy_name: str
    parameters: Dict[str, Any]
