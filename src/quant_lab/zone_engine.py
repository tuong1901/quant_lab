"""
Zone Registry & Dynamic Buffer Engine for M15 BTCUSDT Pipeline Quant Lab.
Loads dynamic Fibo/Key zones from config/zones.yaml and computes dynamic ATR buffers.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import yaml


def load_active_zones(yaml_path: str) -> List[Dict[str, Any]]:
    """
    [PURPOSE]: Read active zone definitions from configuration file.
    [DEPENDENCIES]: Called by Zone Engine initialization.
    [ARGS]: yaml_path — Path to zones.yaml configuration file.
    [RETURNS]: List[Dict] — List of active zone dictionaries.
    [SIDE EFFECTS]: Reads YAML file from disk.
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    zones = config.get('zones', [])
    active_zones = [z for z in zones if z.get('active', True)]
    return active_zones


def filter_zones_by_preset(zones: List[Dict[str, Any]], preset: str) -> List[Dict[str, Any]]:
    """
    [PURPOSE]: Filter zone registry according to selected hyperparameter preset.
    [DEPENDENCIES]: Called by optimization pipeline with preset choice.
    [ARGS]: zones — Full active zone registry.
            preset — Category choice ('tier1_only', 'tier1_plus_extension', 'full_with_harmonic').
    [RETURNS]: List[Dict] — Subset of zones matching preset tier criteria.
    [SIDE EFFECTS]: None (pure function).
    """
    if preset == 'tier1_only':
        return [z for z in zones if z.get('tier', 1) == 1]
    elif preset == 'tier1_plus_extension':
        return [z for z in zones if z.get('tier', 1) in (1, 2)]
    elif preset == 'full_with_harmonic':
        return [z for z in zones if z.get('tier', 1) in (1, 2, 3)]
    else:
        return zones


def compute_dynamic_zone_bounds(
    zone: Dict[str, Any],
    atr_val: float,
    buffer_k: float,
    anchor_range: float
) -> Tuple[float, float]:
    """
    [PURPOSE]: Calculate dynamic upper and lower price bounds for a given zone using ATR buffers.
    [DEPENDENCIES]: Called by State Machine during bar evaluation.
    [ARGS]: zone — Single zone dict.
            atr_val — Wilder RMA ATR value.
            buffer_k — Buffer multiplier.
            anchor_range — Reference swing range price delta.
    [RETURNS]: Tuple[float, float] — (zone_price_lower, zone_price_upper).
    [SIDE EFFECTS]: None (pure function).
    """
    base_lower = zone['lower']
    base_upper = zone['upper']
    mid_ratio = (base_lower + base_upper) / 2.0
    buffer = buffer_k * atr_val
    
    zone_mid_price = mid_ratio * anchor_range
    zone_price_lower = zone_mid_price - buffer
    zone_price_upper = zone_mid_price + buffer
    
    return zone_price_lower, zone_price_upper
