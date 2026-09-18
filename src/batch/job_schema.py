"""
[PURPOSE]: Batch Job specification schema.
[DEPENDENCIES]: None.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class BatchJobSpec:
    job_id: str
    strategy_class: str
    params: Dict[str, Any]
    symbol: str
    timeframe: str
