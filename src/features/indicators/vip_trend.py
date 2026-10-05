"""VIP Trend indicator: trend ribbons, BUY/SELL/WARNING signals, and orchestration."""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.features.indicators.atr import calculate_causal_atr


def calculate_trend_chinh(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    atr_period: int = 14,
    multiplier: float = 3.0,
    dev_factor: float = 0.5,
    initial_tc1: Optional[float] = None,
    initial_atr: Optional[float] = None,
) -> Tuple[List[float], List[float], List[float]]:
    """
    [PURPOSE]: Compute the three stepped Trend Chinh ribbon lines from causal ATR.
    [DEPENDENCIES]: Calls calculate_causal_atr from the ATR indicator module.
    [ARGS]: highs, lows, closes — price series; remaining values configure or anchor the ratchet.
    [RETURNS]: Center, upper, and lower Trend Chinh lines.
    [SIDE EFFECTS]: None (pure calculation).
    """
    count = len(closes)
    price_frame = pd.DataFrame(
        {"open": closes, "high": highs, "low": lows, "close": closes}
    )
    atr = calculate_causal_atr(price_frame, period=atr_period)

    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / atr_period
        for index in range(1, count):
            true_range = max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
            atr[index] = alpha * true_range + (1.0 - alpha) * atr[index - 1]

    trend_chinh_1 = [0.0] * count
    trend_chinh_2 = [0.0] * count
    trend_chinh_3 = [0.0] * count
    if count == 0:
        return trend_chinh_1, trend_chinh_2, trend_chinh_3

    is_uptrend = True
    current_line = (
        initial_tc1 if initial_tc1 is not None else lows[0] - multiplier * atr[0]
    )
    for index in range(count):
        close = closes[index]
        high = highs[index]
        low = lows[index]
        current_atr = atr[index]
        offset = dev_factor * current_atr
        up_bound = low - multiplier * current_atr
        down_bound = high + multiplier * current_atr

        if is_uptrend:
            current_line = max(current_line, up_bound)
            if close < current_line:
                is_uptrend = False
                current_line = down_bound
        else:
            current_line = min(current_line, down_bound)
            if close > current_line:
                is_uptrend = True
                current_line = up_bound

        trend_chinh_1[index] = round(current_line, 2)
        trend_chinh_2[index] = round(current_line + offset, 2)
        trend_chinh_3[index] = round(current_line - offset, 2)

    return trend_chinh_1, trend_chinh_2, trend_chinh_3


def calculate_trend_phu(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    fast_period: int = 14,
    fast_mult: float = 1.0,
    lag_bars: int = 2,
    initial_tp1: Optional[float] = None,
    initial_atr: Optional[float] = None,
) -> Tuple[List[float], List[float]]:
    """
    [PURPOSE]: Compute the fast Trend Phu ratchet and its lagged confirmation line.
    [DEPENDENCIES]: Calls calculate_causal_atr from the ATR indicator module.
    [ARGS]: highs, lows, closes — price series; remaining values configure or anchor the ratchet.
    [RETURNS]: Trend Phu primary and lagged lines.
    [SIDE EFFECTS]: None (pure calculation).
    """
    count = len(closes)
    price_frame = pd.DataFrame(
        {"open": closes, "high": highs, "low": lows, "close": closes}
    )
    atr = calculate_causal_atr(price_frame, period=fast_period)

    if initial_atr is not None and len(atr) > 0:
        atr[0] = initial_atr
        alpha = 1.0 / fast_period
        for index in range(1, count):
            true_range = max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
            atr[index] = alpha * true_range + (1.0 - alpha) * atr[index - 1]

    trend_phu_1 = [0.0] * count
    trend_phu_2 = [0.0] * count
    if count == 0:
        return trend_phu_1, trend_phu_2

    is_uptrend = True
    current_line = (
        initial_tp1 if initial_tp1 is not None else lows[0] - fast_mult * atr[0]
    )
    for index in range(count):
        close = closes[index]
        high = highs[index]
        low = lows[index]
        current_atr = atr[index]
        up_bound = low - fast_mult * current_atr
        down_bound = high + fast_mult * current_atr

        if is_uptrend:
            if up_bound > current_line:
                current_line = up_bound
        else:
            if down_bound < current_line:
                current_line = down_bound

        trend_phu_1[index] = round(current_line, 2)
        trend_phu_2[index] = (
            trend_phu_1[0] if index < lag_bars else trend_phu_1[index - lag_bars]
        )

    return trend_phu_1, trend_phu_2


def generate_signals(
    closes: List[float],
    tc1: List[float],
    tc2: List[float],
    tc3: List[float],
    tp1: List[float],
    tp2: List[float],
) -> List[int]:
    """
    [PURPOSE]: Generate VIP Trend HOLD, SELL, BUY, and WARNING flags from its trend lines.
    [DEPENDENCIES]: Called by compute_indicator_system after Trend Chinh and Trend Phu calculation.
    [ARGS]: closes — close prices; tc1/tc2/tc3 and tp1/tp2 — VIP Trend line series.
    [RETURNS]: Integer flags: 0 HOLD, 1 SELL, 2 BUY, 4 WARNING.
    [SIDE EFFECTS]: None (pure calculation).
    """
    signals = [0] * len(closes)
    for index in range(1, len(closes)):
        close = closes[index]
        previous_close = closes[index - 1]
        is_bull_regime = close > tc1[index]
        is_bear_regime = close < tc1[index]
        tp_crossed_above = tp1[index] > tp2[index] and tp1[index - 1] <= tp2[index - 1]
        tp_crossed_below = tp1[index] < tp2[index] and tp1[index - 1] >= tp2[index - 1]
        tp_bull_expansion = tp1[index] > tp1[index - 1] and tp1[index - 1] == tp2[index - 1]
        tp_bear_expansion = tp1[index] < tp1[index - 1] and tp1[index - 1] == tp2[index - 1]

        if is_bull_regime and tp1[index] >= tp2[index] and tp1[index] > tc1[index]:
            if tp_crossed_above or tp_bull_expansion or (
                previous_close <= tc1[index - 1] and close > tc1[index]
            ):
                signals[index] = 2
                continue

        if is_bear_regime and tp1[index] <= tp2[index] and tp1[index] < tc1[index]:
            if tp_crossed_below or tp_bear_expansion or (
                previous_close >= tc1[index - 1] and close < tc1[index]
            ):
                signals[index] = 1
                continue

        if is_bull_regime and (tp_crossed_below or (close >= tc2[index] and close < previous_close)):
            signals[index] = 4
        elif is_bear_regime and (tp_crossed_above or (close <= tc3[index] and close > previous_close)):
            signals[index] = 4

    return signals


def compute_indicator_system(
    candles: List[Dict[str, Any]],
    tc_atr_period: int = 14,
    tc_multiplier: float = 3.0,
    dev_factor: float = 0.5,
    tp_fast_period: int = 14,
    tp_multiplier: float = 1.0,
    anchor_first_bar: bool = True,
) -> List[Dict[str, Any]]:
    """
    [PURPOSE]: Add all VIP Trend lines and signal flags to each input candle.
    [DEPENDENCIES]: Calls Trend Chinh, Trend Phu, and signal logic in this indicator module.
    [ARGS]: candles — OHLC dictionaries; remaining values configure the VIP Trend calculation.
    [RETURNS]: New candle dictionaries with trend_chinh, trend_phu, and signal fields.
    [SIDE EFFECTS]: None (does not mutate input candle dictionaries).
    """
    if not candles:
        return []

    highs = [float(candle["high"]) for candle in candles]
    lows = [float(candle["low"]) for candle in candles]
    closes = [float(candle["close"]) for candle in candles]
    first_candle = candles[0]
    initial_tc1 = float(first_candle["tc1"]) if anchor_first_bar and "tc1" in first_candle else None
    initial_tp1 = float(first_candle["tp1"]) if anchor_first_bar and "tp1" in first_candle else None
    initial_atr = None
    if anchor_first_bar and "tc1" in first_candle and "tc2" in first_candle:
        initial_atr = (float(first_candle["tc2"]) - float(first_candle["tc1"])) * 2.0

    tc1, tc2, tc3 = calculate_trend_chinh(
        highs,
        lows,
        closes,
        atr_period=tc_atr_period,
        multiplier=tc_multiplier,
        dev_factor=dev_factor,
        initial_tc1=initial_tc1,
        initial_atr=initial_atr,
    )
    tp1, tp2 = calculate_trend_phu(
        highs,
        lows,
        closes,
        fast_period=tp_fast_period,
        fast_mult=tp_multiplier,
        lag_bars=2,
        initial_tp1=initial_tp1,
        initial_atr=initial_atr,
    )
    signals = generate_signals(closes, tc1, tc2, tc3, tp1, tp2)

    results = []
    for index, candle in enumerate(candles):
        result = dict(candle)
        result["trend_chinh_1"] = tc1[index]
        result["trend_chinh_2"] = tc2[index]
        result["trend_chinh_3"] = tc3[index]
        result["trend_phu_1"] = tp1[index]
        result["trend_phu_2"] = tp2[index]
        result["signal"] = signals[index]
        results.append(result)

    return results
