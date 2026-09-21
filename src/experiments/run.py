"""
[PURPOSE]: Define immutable data model for a single ExperimentRun execution unit.
[DEPENDENCIES]: dataclasses, typing, src.experiments.window.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from src.experiments.window import TimeWindow

@dataclass(frozen=True)
class ExperimentRun:
    """
    [PURPOSE]: Immutable specification of an individual experiment run.
    [DEPENDENCIES]: TimeWindow.
    [ARGS]:
        run_id — Unique string identifier for the run (e.g. 'btc_rolling_001').
        window — TimeWindow instance specifying time boundaries.
        seed — Integer random seed for 100% deterministic reproducibility.
        metadata — Additional key-value metadata dictionary.
    [RETURNS]: ExperimentRun instance.
    [SIDE EFFECTS]: None.
    """
    run_id: str
    window: TimeWindow
    seed: int = 42
    metadata: Dict[str, Any] = field(default_factory=dict)
