"""
Data Feed & Causal Feature Engine for M15 BTCUSDT Pipeline Quant Lab.
Handles CSV data loading, Wilder RMA ATR calculation, and causal swing high/low identification.
"""

from typing import List, Dict, Tuple, Any
import numpy as np
import pandas as pd
import yaml


def load_m15_ohlcv(csv_path: str) -> pd.DataFrame:
    """
    [PURPOSE]: Load M15 OHLCV dataset from CSV into a clean pandas DataFrame.
    [DEPENDENCIES]: Called by data feed initialization in run_pipeline.py.
    [ARGS]: csv_path — Path to input CSV file containing OHLCV columns.
    [RETURNS]: pd.DataFrame with normalized columns ['time', 'open', 'high', 'low', 'close', 'volume'].
    [SIDE EFFECTS]: Reads CSV file from disk.
    """
    df = pd.read_csv(csv_path)
    col_map = {col: col.lower().strip() for col in df.columns}
    df = df.rename(columns=col_map)
    
    required_cols = ['open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' missing from dataset {csv_path}")
            
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    if 'volume' in df.columns:
        df['volume'] = df['volume'].astype(float)
    else:
        df['volume'] = 1.0
        
    return df


def calculate_causal_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """
    [PURPOSE]: Compute causal Average True Range (ATR) using Wilder's RMA method.
    [DEPENDENCIES]: Called by Zone Engine and ATR Ratchet module; matches indicator_vip.pine.
    [ARGS]: df — DataFrame containing ['open', 'high', 'low', 'close'].
            period — Lookback smoothing period (default 14).
    [RETURNS]: np.ndarray — Array of smoothed ATR values.
    [SIDE EFFECTS]: None (pure calculation).
    """
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()
    n = len(closes)
    
    if n == 0:
        return np.array([])
        
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        
    atr = np.zeros(n)
    if n < period:
        atr[:] = np.mean(tr)
        return atr
        
    initial_sma = np.mean(tr[:period])
    atr[:period] = initial_sma
    alpha = 1.0 / float(period)
    
    curr_atr = initial_sma
    for i in range(period, n):
        curr_atr = alpha * tr[i] + (1.0 - alpha) * curr_atr
        atr[i] = curr_atr
        
    return atr


def calculate_causal_swings(df: pd.DataFrame, lookback: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    [PURPOSE]: Identify causal swing high and swing low pivot points.
    [DEPENDENCIES]: Called by Projection Engine to compute swing ranges.
    [ARGS]: df — DataFrame with ['high', 'low'].
            lookback — Half-window size for swing pivot detection.
    [RETURNS]: Tuple of (swing_highs, swing_lows, confirmed_at_bar).
    [SIDE EFFECTS]: None (pure calculation).
    """
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    n = len(highs)
    
    swing_highs = np.full(n, np.nan)
    swing_lows = np.full(n, np.nan)
    confirmed_at = np.full(n, -1, dtype=int)
    
    for i in range(lookback, n - lookback):
        window_highs = highs[i - lookback : i + lookback + 1]
        window_lows = lows[i - lookback : i + lookback + 1]
        
        is_pivot_high = (highs[i] == np.max(window_highs))
        is_pivot_low = (lows[i] == np.min(window_lows))
        
        confirmation_bar = i + lookback
        if is_pivot_high:
            swing_highs[confirmation_bar] = highs[i]
            confirmed_at[confirmation_bar] = confirmation_bar
        if is_pivot_low:
            swing_lows[confirmation_bar] = lows[i]
            confirmed_at[confirmation_bar] = confirmation_bar
            
    latest_sh = np.nan
    latest_sl = np.nan
    for i in range(n):
        if not np.isnan(swing_highs[i]):
            latest_sh = swing_highs[i]
        if not np.isnan(swing_lows[i]):
            latest_sl = swing_lows[i]
        swing_highs[i] = latest_sh
        swing_lows[i] = latest_sl
        
    return swing_highs, swing_lows, confirmed_at
