"""
Script to capture Golden Behavioral Baseline snapshot from legacy pipeline.
Exports tests/fixtures/golden_baseline_v1.json.
"""

import os
import sys
import json
import yaml
import hashlib
import pandas as pd
import numpy as np

# Add repo root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.quant_lab.data_feed import load_m15_ohlcv, calculate_causal_atr, calculate_causal_swings
from src.quant_lab.execution_simulator import run_trade_simulation
from src.quant_lab.optimizer import run_optuna_study


def main():
    dataset_path = 'data/valm15-indivip_signal.csv'
    if not os.path.exists(dataset_path):
        dataset_path = 'data/testm15_indi.csv'
        
    print(f"Capturing Golden Baseline from dataset: {dataset_path}")
    
    with open(dataset_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    df = load_m15_ohlcv(dataset_path)
    
    with open('config/zones.yaml', 'r', encoding='utf-8') as f:
        zones_cfg = yaml.safe_load(f)
    with open('config/fixed_params.yaml', 'r', encoding='utf-8') as f:
        fixed_cfg = yaml.safe_load(f)
    with open('config/search_space.yaml', 'r', encoding='utf-8') as f:
        space_cfg = yaml.safe_load(f)
        
    atr_period = fixed_cfg.get('atr_ratchet', {}).get('period', 14)
    atr_series = calculate_causal_atr(df, period=atr_period)
    swings = calculate_causal_swings(df, lookback=20)
    
    # Run 10 Optuna trials on first 10,000 bars for deterministic baseline
    df_slice = df.iloc[:min(len(df), 10000)].copy()
    atr_slice = atr_series[:len(df_slice)]
    swings_slice = (swings[0][:len(df_slice)], swings[1][:len(df_slice)], swings[2][:len(df_slice)])
    
    champion_params = run_optuna_study(
        df_slice, atr_slice, swings_slice, space_cfg, fixed_cfg, n_trials=10
    )
    
    trades, equity = run_trade_simulation(
        df_slice, atr_slice, swings_slice, champion_params, fixed_cfg, fill_mode='bar_close'
    )
    
    golden_data = {
        'dataset': dataset_path,
        'dataset_sha256': file_hash,
        'bars_evaluated': len(df_slice),
        'champion_params': champion_params,
        'total_trades': len(trades),
        'final_equity': float(equity[-1]),
        'trades': trades,
        'equity_curve': [float(e) for e in equity]
    }
    
    out_dir = 'tests/fixtures'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'golden_baseline_v1.json')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(golden_data, f, indent=2)
        
    print(f"Golden Baseline captured successfully! Saved {len(trades)} trades and equity curve to {out_path}")


if __name__ == '__main__':
    main()
