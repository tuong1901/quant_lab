"""
Multi-Horizon OOS & Alpha Decay Tracker for M15 BTCUSDT Pipeline Quant Lab.
Performs dual-axis out-of-sample degradation testing across time horizons ([3M], [6M], [1Y])
and trade-count normalized horizons ([50], [100], [250] trades).
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from src.quant_lab.execution_simulator import run_trade_simulation


def evaluate_time_horizons(
    df_oos: pd.DataFrame,
    atr_oos: np.ndarray,
    swings_oos: Tuple[np.ndarray, np.ndarray, np.ndarray],
    params: Dict[str, Any],
    fixed_config: Dict[str, Any]
) -> Dict[str, Dict[str, float]]:
    """
    [PURPOSE]: Evaluate strategy OOS degradation across parallel time horizons [3M], [6M], [1Y].
    [DEPENDENCIES]: Calls run_trade_simulation().
    [ARGS]: df_oos — Out-of-sample DataFrame.
            atr_oos — Out-of-sample ATR array.
            swings_oos — Out-of-sample swings tuple.
            params — Optimized strategy parameters.
            fixed_config — Fixed configuration parameters.
    [RETURNS]: Dict — Telemetry dictionary with metrics for 3M, 6M, and 1Y slices.
    [SIDE EFFECTS]: None.
    """
    bar_horizons = {
        '3M': min(len(df_oos), 8760),
        '6M': min(len(df_oos), 17520),
        '1Y': min(len(df_oos), 35040)
    }

    results = {}
    for horizon_label, n_bars in bar_horizons.items():
        if n_bars <= 100:
            continue
            
        df_sub = df_oos.iloc[:n_bars].copy()
        atr_sub = atr_oos[:n_bars]
        swings_sub = (swings_oos[0][:n_bars], swings_oos[1][:n_bars], swings_oos[2][:n_bars])

        trades, eq = run_trade_simulation(df_sub, atr_sub, swings_sub, params, fixed_config)
        
        if len(trades) == 0:
            results[horizon_label] = {'trades': 0, 'expectancy': 0.0, 'sharpe': 0.0, 'win_rate': 0.0}
            continue

        r_mults = [t['r_multiple'] for t in trades]
        net_pnls = [t['net_pnl'] for t in trades]
        wins = [t for t in trades if t['net_pnl'] > 0]

        returns = np.diff(eq) / eq[:-1]
        std_ret = np.std(returns)
        sharpe = (np.mean(returns) / max(1e-9, std_ret)) * np.sqrt(35040)

        results[horizon_label] = {
            'trades': len(trades),
            'expectancy': float(np.mean(net_pnls)),
            'avg_r': float(np.mean(r_mults)),
            'sharpe': float(sharpe),
            'win_rate': float(len(wins) / len(trades))
        }

    return results


def evaluate_trade_count_horizons(
    trades_full: List[Dict[str, Any]]
) -> Dict[str, Dict[str, float]]:
    """
    [PURPOSE]: Evaluate strategy degradation across trade-count normalized horizons [50], [100], [250] trades.
    [DEPENDENCIES]: Takes trade history output from run_trade_simulation().
    [ARGS]: trades_full — List of complete trade records.
    [RETURNS]: Dict — Telemetry dictionary for 50, 100, 250 trade slices.
    [SIDE EFFECTS]: None.
    """
    trade_horizons = {'50_trades': 50, '100_trades': 100, '250_trades': 250}
    results = {}

    for label, count in trade_horizons.items():
        sub_trades = trades_full[:count]
        if len(sub_trades) == 0:
            results[label] = {'trades': 0, 'expectancy': 0.0, 'avg_r': 0.0, 'win_rate': 0.0}
            continue

        r_mults = [t['r_multiple'] for t in sub_trades]
        net_pnls = [t['net_pnl'] for t in sub_trades]
        wins = [t for t in sub_trades if t['net_pnl'] > 0]

        results[label] = {
            'trades': len(sub_trades),
            'expectancy': float(np.mean(net_pnls)),
            'avg_r': float(np.mean(r_mults)),
            'win_rate': float(len(wins) / len(sub_trades))
        }

    return results


def compute_alpha_decay_summary(
    time_results: Dict[str, Dict[str, float]],
    trade_results: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    [PURPOSE]: Synthesize dual-axis degradation telemetry into alpha decay slope and verdict flags.
    [DEPENDENCIES]: Called by reporting module.
    [ARGS]: time_results — Output from evaluate_time_horizons().
            trade_results — Output from evaluate_trade_count_horizons().
    [RETURNS]: Dict — Alpha decay telemetry summary.
    [SIDE EFFECTS]: None.
    """
    sharpe_3m = time_results.get('3M', {}).get('sharpe', 0.0)
    sharpe_1y = time_results.get('1Y', {}).get('sharpe', 0.0)
    
    decay_ratio = (sharpe_1y / max(1e-4, sharpe_3m)) if sharpe_3m > 0 else 0.0

    return {
        'time_horizons': time_results,
        'trade_count_horizons': trade_results,
        'alpha_decay_ratio': float(decay_ratio),
        'decay_verdict': 'STABLE' if decay_ratio >= 0.70 else ('DECAYING' if decay_ratio >= 0.40 else 'SEVERE_DECAY')
    }
