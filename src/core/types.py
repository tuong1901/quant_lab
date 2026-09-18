"""
[PURPOSE]: Define core system types, enums, and data models.
[DEPENDENCIES]: None.
[ARGS]: N/A.
[RETURNS]: N/A.
[SIDE EFFECTS]: None.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class TimeFrame(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
