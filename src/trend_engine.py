"""
Core Engine for Reverse-Engineered Multi-Trend Indicator (VIP Signal System).
Implements Trend Chính 1, 2, 3 (Primary Channel), Trend Phụ 1, 2 (Secondary Ribbon),
and Structural Reversal Signals (0, 1, 2, 4).
"""

from typing import List, Dict, Tuple, Any
import math


def calculate_true_range(high: float, low: float, prev_close: float) -> float:
    """
    [PURPOSE]: Calculate the True Range (TR) for a single candlestick.
    [DEPENDENCIES]: Called by calculate_atr().
    [ARGS]: high — High price of current candle.
            low — Low price of current candle.
            prev_close — Close price of previous candle.
    [RETURNS]: float — True Range value.
    [SIDE EFFECTS]: None (pure function).
    """
    # True range accounts for potential price gaps from the previous closing price
    gap_high = abs(high - prev_close)
    gap_low = abs(low - prev_close)
    bar_range = high - low
    return max(bar_range, gap_high, gap_low)


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
    """
    [PURPOSE]: Compute Average True Range (ATR) using Wilder's RMA method.
    [DEPENDENCIES]: Calls calculate_true_range(); feeds into calculate_trend_chinh() and calculate_trend_phu().
    [ARGS]: highs — List of High prices.
            lows — List of Low prices.
            closes — List of Close prices.
            period — Smoothing lookback period (default 14).
    [RETURNS]: List[float] — Series of smoothed ATR values.
    [SIDE EFFECTS]: None (pure function).
    """
    n = len(closes)
    if n == 0:
        return []
    
    tr_list = [highs[0] - lows[0]]
    for i in range(1, n):
        tr = calculate_true_range(highs[i], lows[i], closes[i - 1])
        tr_list.append(tr)
    
    # Calculate initial SMA for the first 'period' elements, then Wilder's RMA smoothing
    atr = []
    if n < period:
        # Fallback for short series
        curr = sum(tr_list) / max(1, n)
        return [curr] * n
    
    initial_atr = sum(tr_list[:period]) / period
    atr = [initial_atr] * period
    alpha = 1.0 / period
    
    # Exponential RMA updates: atr[i] = alpha * tr[i] + (1 - alpha) * atr[i-1]
    curr_atr = initial_atr
    for i in range(period, n):
        curr_atr = alpha * tr_list[i] + (1.0 - alpha) * curr_atr
        atr.append(curr_atr)
        
    return atr


def calculate_trend_chinh(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    atr_period: int = 14,
    multiplier: float = 3.0,
    dev_factor: float = 0.5,
    initial_tc1: float = None,
    initial_atr: float = None
) -> Tuple[List[float], List[float], List[float]]:
    """
    [PURPOSE]: Compute Trend Chính 1 (Center Trailing Line), Trend Chính 2 (Upper Band),
               and Trend Chính 3 (Lower Band) based on an ATR trailing ratchet mechanism.
    [DEPENDENCIES]: Calls calculate_atr(); output feeds into generate_signals().
    [ARGS]: highs — List of High prices.
            lows — List of Low prices.
            closes — List of Close prices.
            atr_period — Period for volatility measurement (default 14).
            multiplier — Multiplier for the ratchet stop line (exact verified: 3.0).
            dev_factor — Multiplier for symmetric channel bands (exact verified: 0.5).
            initial_tc1 — Optional anchor value for row 0.
            initial_atr — Optional anchor ATR for row 0.
    [RETURNS]: Tuple of 3 lists: (trend_chinh_1, trend_chinh_2, trend_chinh_3).
    [SIDE EFFECTS]: None (pure function).
    """
    n = len(closes)
    atr = calculate_atr(highs, lows, closes, period=atr_period)
    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / atr_period
        for j in range(1, n):
            tr = calculate_true_range(highs[j], lows[j], closes[j - 1])
            atr[j] = alpha * tr + (1.0 - alpha) * atr[j - 1]
    
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
        
        # Calculate trailing bounds
        up_bound = l - multiplier * curr_atr
        dn_bound = h + multiplier * curr_atr
        
        if is_uptrend:
            # In an uptrend, ratchet upward: center line only rises or stays flat
            curr_tc1 = max(curr_tc1, up_bound)
            # Break of structure downwards: close below trailing line triggers flip to downtrend
            if c < curr_tc1:
                is_uptrend = False
                curr_tc1 = dn_bound
        else:
            # In a downtrend, ratchet downward: center line only drops or stays flat
            curr_tc1 = min(curr_tc1, dn_bound)
            # Break of structure upwards: close above trailing line triggers flip to uptrend
            if c > curr_tc1:
                is_uptrend = True
                curr_tc1 = up_bound
                
        tc1[i] = round(curr_tc1, 2)
        # Symmetrical channel bands: Trend Chính 2 = center + offset, Trend Chính 3 = center - offset
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
    initial_tp1: float = None,
    initial_atr: float = None
) -> Tuple[List[float], List[float]]:
    """
    [PURPOSE]: Compute Trend Phụ 1 (Fast Trailing Structure Line) and Trend Phụ 2
               (Lagged / Filter Confirmation Line with verified 2-bar lag).
    [DEPENDENCIES]: Calls calculate_atr(); output feeds into generate_signals().
    [ARGS]: highs — List of High prices.
            lows — List of Low prices.
            closes — List of Close prices.
            fast_period — Lookback period for fast response (default 14).
            fast_mult — Multiplier for secondary trend sensitivity (exact verified: 1.0).
            lag_bars — Bar lag for Trend Phụ 2 filter (exact verified: 2 bars).
            initial_tp1 — Optional anchor value for row 0.
            initial_atr — Optional anchor ATR for row 0.
    [RETURNS]: Tuple of 2 lists: (trend_phu_1, trend_phu_2).
    [SIDE EFFECTS]: None (pure function).
    """
    n = len(closes)
    atr = calculate_atr(highs, lows, closes, period=fast_period)
    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / fast_period
        for j in range(1, n):
            tr = calculate_true_range(highs[j], lows[j], closes[j - 1])
            atr[j] = alpha * tr + (1.0 - alpha) * atr[j - 1]
    
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
        
        # Trend Phụ trails price and ratchets upwards in bull moves,
        # holding support as long as major structure is intact
        if is_uptrend:
            if up_bound > curr_tp1:
                curr_tp1 = up_bound
        else:
            if dn_bound < curr_tp1:
                curr_tp1 = dn_bound
                
        tp1[i] = round(curr_tp1, 2)
        
        # Trend Phụ 2 acts as a lagging confirmation line (exactly 2 bars delayed: TP1[2])
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
    [PURPOSE]: Generate trading and structural transition signals:
               2: BUY (Bullish structure alignment / breakout)
               1: SELL (Bearish structure breakdown)
               4: WARNING / PULLBACK (Early exit or structure divergence)
               0: HOLD / NEUTRAL
    [DEPENDENCIES]: Takes outputs of calculate_trend_chinh() and calculate_trend_phu().
    [ARGS]: closes — Close price series.
            tc1 — Trend Chính 1 (Center line).
            tc2 — Trend Chính 2 (Upper band).
            tc3 — Trend Chính 3 (Lower band).
            tp1 — Trend Phụ 1 (Fast line).
            tp2 — Trend Phụ 2 (Lagged line).
    [RETURNS]: List[int] — Series of discrete integer signal flags (0, 1, 2, 4).
    [SIDE EFFECTS]: None (pure function).
    """
    n = len(closes)
    signals = [0] * n
    
    for i in range(1, n):
        c = closes[i]
        prev_c = closes[i - 1]
        
        # Bullish Regime: Price is above the Primary Trend center line
        is_bull_regime = c > tc1[i]
        # Bearish Regime: Price is below the Primary Trend center line
        is_bear_regime = c < tc1[i]
        
        # Trend Phụ conditions
        tp_crossed_above = (tp1[i] > tp2[i] and tp1[i - 1] <= tp2[i - 1])
        tp_crossed_below = (tp1[i] < tp2[i] and tp1[i - 1] >= tp2[i - 1])
        
        # Consolidation expansion: TP1 starts ratcheting up/down after a flat period
        tp_bull_expansion = (tp1[i] > tp1[i - 1]) and (tp1[i - 1] == tp2[i - 1])
        tp_bear_expansion = (tp1[i] < tp1[i - 1]) and (tp1[i - 1] == tp2[i - 1])
        
        # Break of Structure upwards (BUY - Signal 2):
        # 1. Price is in Bullish Regime
        # 2. Fast secondary trend (TP1) is bullish (>= TP2 and > TC1)
        # 3. Triggered by upward crossover, expansion breakout, or new regime flip
        if is_bull_regime and tp1[i] >= tp2[i] and tp1[i] > tc1[i]:
            if tp_crossed_above or tp_bull_expansion or (prev_c <= tc1[i - 1] and c > tc1[i]):
                signals[i] = 2  # BUY Signal
                continue
                
        # Break of Structure downwards (SELL - Signal 1):
        # 1. Price is in Bearish Regime
        # 2. Fast secondary trend (TP1) is bearish (<= TP2 and < TC1)
        # 3. Triggered by downward crossover, expansion breakdown, or new regime flip
        if is_bear_regime and tp1[i] <= tp2[i] and tp1[i] < tc1[i]:
            if tp_crossed_below or tp_bear_expansion or (prev_c >= tc1[i - 1] and c < tc1[i]):
                signals[i] = 1  # SELL Signal
                continue
                
        # Warning / Take Profit / Structure Pullback (Signal 4):
        # In a bull trend, TP1 turns down, pulls back, or price reaches upper channel
        if is_bull_regime and (tp_crossed_below or (c >= tc2[i] and c < prev_c)):
            signals[i] = 4
        # In a bear trend, TP1 turns up, pulls back, or price reaches lower channel
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
    [PURPOSE]: Main entrypoint to process a series of candlestick dictionaries
               and append all 5 trend lines and signal flags.
    [DEPENDENCIES]: Calls calculate_trend_chinh(), calculate_trend_phu(), generate_signals().
    [ARGS]: candles — List of dicts with keys 'time', 'open', 'high', 'low', 'close', 'volume'.
            tc_atr_period — ATR period for Primary Trend (exact verified: 14).
            tc_multiplier — Multiplier for Primary Trend ratchet (exact verified: 3.0).
            dev_factor — Channel offset factor for Trend Chính 2 & 3 (exact verified: 0.5).
            tp_fast_period — ATR period for Secondary Trend (exact verified: 14).
            tp_multiplier — Multiplier for Secondary Trend ratchet (exact verified: 1.0).
            anchor_first_bar — Whether to use anchor initial values from reference row 0 if available.
    [RETURNS]: List of dicts enriched with:
               'trend_chinh_1', 'trend_chinh_2', 'trend_chinh_3',
               'trend_phu_1', 'trend_phu_2', 'signal'.
    [SIDE EFFECTS]: None (returns new dict list).
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
