"""
Feature Engineering Subsystem (`src/features`).
"""

from src.features.indicators import (
    calculate_causal_atr,
    calculate_causal_swings,
    calculate_trend_chinh,
    calculate_trend_phu,
    generate_signals,
    compute_indicator_system,
)
from src.features.fibo import FIBO_1_LEVELS, get_fibo_1_levels
from src.features.candle import add_candle_anatomy, add_candle_normalization, add_reversal_patterns
from src.features.zones import (
    load_active_zones,
    filter_zones_by_preset,
    compute_dynamic_zone_bounds,
    project_target_zone,
)

__all__ = [
    "calculate_causal_atr",
    "FIBO_1_LEVELS",
    "get_fibo_1_levels",
    "add_candle_anatomy",
    "add_candle_normalization",
    "add_reversal_patterns",
    "calculate_causal_swings",
    "calculate_trend_chinh",
    "calculate_trend_phu",
    "generate_signals",
    "compute_indicator_system",
    "load_active_zones",
    "filter_zones_by_preset",
    "compute_dynamic_zone_bounds",
    "project_target_zone",
]
