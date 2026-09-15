"""
Causal Target Projection Engine for M15 BTCUSDT Pipeline Quant Lab.
Projects future target zones prior to price arrival based on confirmed swing ranges and extension ratios.
"""

from typing import Dict, Any, Optional
import numpy as np


def project_target_zone(
    entry_price: float,
    swing_high: float,
    swing_low: float,
    direction: str,
    extension_ratio: float,
    current_bar_idx: int,
    confirmed_at_bar: int
) -> Optional[float]:
    """
    [PURPOSE]: Dynamically project downstream target zone before price arrives.
    [DEPENDENCIES]: Called by State Machine upon entry zone touch.
    [ARGS]: entry_price — Entry level price.
            swing_high — Confirmed swing high price.
            swing_low — Confirmed swing low price.
            direction — Trade direction ('long' or 'short').
            extension_ratio — Extension projection hyperparameter ratio.
            current_bar_idx — Current bar evaluation index.
            confirmed_at_bar — Bar index when the swing high/low was confirmed.
    [RETURNS]: Optional[float] — Projected target price level.
    [SIDE EFFECTS]: Enforces strict causality guardrails.
    """
    if confirmed_at_bar > current_bar_idx:
        raise ValueError(
            f"Causality violation! Swing confirmed at bar {confirmed_at_bar} "
            f"cannot be used at bar {current_bar_idx}."
        )
        
    swing_range = abs(swing_high - swing_low)
    if swing_range <= 0:
        return None
        
    if direction == 'long':
        target_price = entry_price + (swing_range * extension_ratio)
    else:
        target_price = entry_price - (swing_range * extension_ratio)
        
    return target_price
