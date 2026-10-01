"""
[PURPOSE]: Causal Technical Indicators & Trend Ribbon Feature Engine (`src/features/indicators.py`).
[DEPENDENCIES]: numpy, pandas, typing.
"""

from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import pandas as pd


def calculate_causal_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """
    [PURPOSE]: Compute causal Average True Range (ATR) using Wilder's RMA method.
    [DEPENDENCIES]: Called by Zone Engine, ATR Ratchet, and Feature Engine.
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


def calculate_causal_swings(df: pd.DataFrame, lookback: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    [PURPOSE]: Identify causal swing high and swing low pivot points.
    [DEPENDENCIES]: Called by Projection Engine and State Machine.
    [ARGS]: df — DataFrame with ['high', 'low'].
            lookback — Half-window size for swing pivot detection (default 20).
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
        
        is_pivot_high = bool(highs[i] == np.max(window_highs))
        is_pivot_low = bool(lows[i] == np.min(window_lows))
        
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


def calculate_trend_chinh(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    atr_period: int = 14,
    multiplier: float = 3.0,
    dev_factor: float = 0.5,
    initial_tc1: Optional[float] = None,
    initial_atr: Optional[float] = None
) -> Tuple[List[float], List[float], List[float]]:
    """
    [PURPOSE]: Compute Trend Chính 1 (Center Trailing Line), Trend Chính 2 (Upper Band),
               and Trend Chính 3 (Lower Band) based on ATR trailing ratchet mechanism.
    [DEPENDENCIES]: Calls calculate_causal_atr().
    [ARGS]: highs, lows, closes — Price series.
            atr_period — ATR period (default 14).
            multiplier — Multiplier for ratchet stop (default 3.0).
            dev_factor — Channel band offset (default 0.5).
            initial_tc1, initial_atr — Optional row 0 anchors.
    [RETURNS]: Tuple of 3 lists: (trend_chinh_1, trend_chinh_2, trend_chinh_3).
    """
    n = len(closes)
    df_temp = pd.DataFrame({'open': closes, 'high': highs, 'low': lows, 'close': closes})
    atr = calculate_causal_atr(df_temp, period=atr_period)
    
    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / atr_period
        for j in range(1, n):
            tr_j = max(highs[j] - lows[j], abs(highs[j] - closes[j - 1]), abs(lows[j] - closes[j - 1]))
            atr[j] = alpha * tr_j + (1.0 - alpha) * atr[j - 1]
    
    tc1 = [0.0] * n
    tc2 = [0.0] * n
    tc3 = [0.0] * n
    
    if n == 0:
        return tc1, tc2, tc3
        
    is_uptrend = True
    curr_tc1 = initial_tc1 if initial_tc1 is not None else (lows[0] - multiplier * atr[0])
    
    for i in range(n):
        c = closes[i]
        h = highs[i]
        l = lows[i]
        curr_atr = atr[i]
        offset = dev_factor * curr_atr
        
        up_bound = l - multiplier * curr_atr
        dn_bound = h + multiplier * curr_atr
        
        if is_uptrend:
            curr_tc1 = max(curr_tc1, up_bound)
            if c < curr_tc1:
                is_uptrend = False
                curr_tc1 = dn_bound
        else:
            curr_tc1 = min(curr_tc1, dn_bound)
            if c > curr_tc1:
                is_uptrend = True
                curr_tc1 = up_bound
                
        tc1[i] = round(curr_tc1, 2)
        tc2[i] = round(curr_tc1 + offset, 2)
        tc3[i] = round(curr_tc1 - offset, 2)
        
    return tc1, tc2, tc3


def calculate_trend_phu(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    fast_period: int = 14,
    fast_mult: float = 1.0,
    lag_bars: int = 2,
    initial_tp1: Optional[float] = None,
    initial_atr: Optional[float] = None
) -> Tuple[List[float], List[float]]:
    """
    [PURPOSE]: Compute Trend Phụ 1 (Fast Trailing Line) and Trend Phụ 2 (Lagged Filter Line).
    [DEPENDENCIES]: Calls calculate_causal_atr().
    [ARGS]: highs, lows, closes — Price series.
            fast_period — Fast ATR period (default 14).
            fast_mult — Fast multiplier (default 1.0).
            lag_bars — Lag offset for TP2 (default 2 bars).
    [RETURNS]: Tuple of 2 lists: (trend_phu_1, trend_phu_2).
    """
    n = len(closes)
    df_temp = pd.DataFrame({'open': closes, 'high': highs, 'low': lows, 'close': closes})
    atr = calculate_causal_atr(df_temp, period=fast_period)
    
    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / fast_period
        for j in range(1, n):
            tr_j = max(highs[j] - lows[j], abs(highs[j] - closes[j - 1]), abs(lows[j] - closes[j - 1]))
            atr[j] = alpha * tr_j + (1.0 - alpha) * atr[j - 1]
    
    tp1 = [0.0] * n
    tp2 = [0.0] * n
    
    if n == 0:
        return tp1, tp2
        
    is_uptrend = True
    curr_tp1 = initial_tp1 if initial_tp1 is not None else (lows[0] - fast_mult * atr[0])
    
    for i in range(n):
        c = closes[i]
        h = highs[i]
        l = lows[i]
        curr_atr = atr[i]
        
        up_bound = l - fast_mult * curr_atr
        dn_bound = h + fast_mult * curr_atr
        
        if is_uptrend:
            if up_bound > curr_tp1:
                curr_tp1 = up_bound
        else:
            if dn_bound < curr_tp1:
                curr_tp1 = dn_bound
                
        tp1[i] = round(curr_tp1, 2)
        
        if i < lag_bars:
            tp2[i] = tp1[0]
        else:
            tp2[i] = tp1[i - lag_bars]
            
    return tp1, tp2


def generate_signals(
    closes: List[float],
    tc1: List[float],
    tc2: List[float],
    tc3: List[float],
    tp1: List[float],
    tp2: List[float]
) -> List[int]:
    """
    [PURPOSE]: Generate discrete integer signal flags (0: HOLD, 1: SELL, 2: BUY, 4: WARNING).
    """
    n = len(closes)
    signals = [0] * n
    
    for i in range(1, n):
        c = closes[i]
        prev_c = closes[i - 1]
        
        is_bull_regime = c > tc1[i]
        is_bear_regime = c < tc1[i]
        
        tp_crossed_above = (tp1[i] > tp2[i] and tp1[i - 1] <= tp2[i - 1])
        tp_crossed_below = (tp1[i] < tp2[i] and tp1[i - 1] >= tp2[i - 1])
        
        tp_bull_expansion = (tp1[i] > tp1[i - 1]) and (tp1[i - 1] == tp2[i - 1])
        tp_bear_expansion = (tp1[i] < tp1[i - 1]) and (tp1[i - 1] == tp2[i - 1])
        
        if is_bull_regime and tp1[i] >= tp2[i] and tp1[i] > tc1[i]:
            if tp_crossed_above or tp_bull_expansion or (prev_c <= tc1[i - 1] and c > tc1[i]):
                signals[i] = 2
                continue
                
        if is_bear_regime and tp1[i] <= tp2[i] and tp1[i] < tc1[i]:
            if tp_crossed_below or tp_bear_expansion or (prev_c >= tc1[i - 1] and c < tc1[i]):
                signals[i] = 1
                continue
                
        if is_bull_regime and (tp_crossed_below or (c >= tc2[i] and c < prev_c)):
            signals[i] = 4
        elif is_bear_regime and (tp_crossed_above or (c <= tc3[i] and c > prev_c)):
            signals[i] = 4
            
    return signals


def compute_indicator_system(
    candles: List[Dict[str, Any]],
    tc_atr_period: int = 14,
    tc_multiplier: float = 3.0,
    dev_factor: float = 0.5,
    tp_fast_period: int = 14,
    tp_multiplier: float = 1.0,
    anchor_first_bar: bool = True
) -> List[Dict[str, Any]]:
    """
    [PURPOSE]: Process candlestick dict list and append trend lines + signals.
    """
    if not candles:
        return []
        
    highs = [float(c['high']) for c in candles]
    lows = [float(c['low']) for c in candles]
    closes = [float(c['close']) for c in candles]
    
    initial_tc1 = float(candles[0]['tc1']) if (anchor_first_bar and 'tc1' in candles[0]) else None
    initial_tp1 = float(candles[0]['tp1']) if (anchor_first_bar and 'tp1' in candles[0]) else None
    initial_atr = None
    if anchor_first_bar and 'tc1' in candles[0] and 'tc2' in candles[0]:
        initial_atr = (float(candles[0]['tc2']) - float(candles[0]['tc1'])) * 2.0
    
    tc1, tc2, tc3 = calculate_trend_chinh(
        highs, lows, closes,
        atr_period=tc_atr_period,
        multiplier=tc_multiplier,
        dev_factor=dev_factor,
        initial_tc1=initial_tc1,
        initial_atr=initial_atr
    )
    
    tp1, tp2 = calculate_trend_phu(
        highs, lows, closes,
        fast_period=tp_fast_period,
        fast_mult=tp_multiplier,
        lag_bars=2,
        initial_tp1=initial_tp1,
        initial_atr=initial_atr
    )
    
    sigs = generate_signals(closes, tc1, tc2, tc3, tp1, tp2)
    
    results = []
    for i, c in enumerate(candles):
        res = dict(c)
        res['trend_chinh_1'] = tc1[i]
        res['trend_chinh_2'] = tc2[i]
        res['trend_chinh_3'] = tc3[i]
        res['trend_phu_1'] = tp1[i]
        res['trend_phu_2'] = tp2[i]
        res['signal'] = sigs[i]
        results.append(res)
        
    return results
