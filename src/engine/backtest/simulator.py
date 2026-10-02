"""
[PURPOSE]: Dual-Fill Execution & Backtest Trade Simulator (`src/engine/simulator.py`).
[DEPENDENCIES]: numpy, pandas, typing, src.strategies.state_machine, src.strategies.atr_ratchet, src.environment.accounting.risk_manager.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

from src.strategies.state_machine import SetupStateMachine
from src.strategies.atr_ratchet import ATRRatchetExit
from src.environment.accounting.risk_manager import calculate_risk_position_size


def run_trade_simulation(
    df: pd.DataFrame,
    atr_series: np.ndarray,
    swings_tuple: Tuple[np.ndarray, np.ndarray, np.ndarray],
    params: Dict[str, Any],
    fixed_config: Dict[str, Any],
    fill_mode: str = 'bar_close'
) -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """
    [PURPOSE]: Execute complete backtest simulation over candle dataset for given hyperparameter set.
    """
    n = len(df)
    if n == 0:
        return [], np.array([])
        
    opens = df['open'].to_numpy()
    highs = df['high'].to_numpy()
    lows = df['low'].to_numpy()
    closes = df['close'].to_numpy()
    
    swing_highs, swing_lows, confirmed_at = swings_tuple
    
    capital_cfg = fixed_config.get('capital_management', {}) if isinstance(fixed_config, dict) else {}
    friction_cfg = fixed_config.get('friction', {}) if isinstance(fixed_config, dict) else {}
    
    init_cap = capital_cfg.get('initial_capital', 10000.0)
    initial_capital = float(init_cap[0] if isinstance(init_cap, (list, tuple)) else init_cap)
    
    r_pct = capital_cfg.get('risk_per_trade_pct', 0.01)
    risk_pct = float(r_pct[0] if isinstance(r_pct, (list, tuple)) else r_pct)
    
    c_bps = friction_cfg.get('commission_bps', 4.0)
    comm_rate = float(c_bps[0] if isinstance(c_bps, (list, tuple)) else c_bps) / 10000.0
    
    s_fac = friction_cfg.get('slippage_atr_factor', 0.05)
    slip_factor = float(s_fac[0] if isinstance(s_fac, (list, tuple)) else s_fac)
    
    use_funding = bool(friction_cfg.get('enable_funding_rate', True))
    
    f_8h = friction_cfg.get('funding_rate_8h', 0.0001)
    funding_8h = float(f_8h[0] if isinstance(f_8h, (list, tuple)) else f_8h)

    stage_timeout = params.get('stage_timeout_bars', 24)
    buffer_k = params.get('zone_buffer_k', 0.5)
    trigger_type = params.get('trigger_candle_type', 'any')
    ratchet_trigger = params.get('ratchet_activation_trigger', 'at_1R')

    ratchet_cfg = fixed_config.get('atr_ratchet', {}) if isinstance(fixed_config, dict) else {}
    mult_raw = ratchet_cfg.get('multiplier', 3.0)
    ratchet_mult = float(mult_raw[0] if isinstance(mult_raw, (list, tuple)) else mult_raw)

    state_machine = SetupStateMachine(timeout_bars=stage_timeout)
    atr_exit = ATRRatchetExit(multiplier=ratchet_mult)

    current_balance = initial_capital
    trades: List[Dict[str, Any]] = []
    equity_curve = np.zeros(n)
    equity_curve[0] = initial_capital

    in_position = False
    pos_direction = None
    pos_entry_price = 0.0
    pos_stop_loss = 0.0
    pos_lot_size = 0.0
    pos_entry_bar = 0

    for i in range(n):
        c_bar = {'open': opens[i], 'high': highs[i], 'low': lows[i], 'close': closes[i]}
        curr_atr = atr_series[i]
        
        sh = swing_highs[i] if not np.isnan(swing_highs[i]) else closes[i] * 1.05
        sl = swing_lows[i] if not np.isnan(swing_lows[i]) else closes[i] * 0.95
        eq_price = (sh + sl) / 2.0

        if not in_position:
            stage, direction, trigger_price = state_machine.update_bar(
                c_bar, curr_atr, eq_price, trigger_type, buffer_k
            )

            if stage == 4 and trigger_price is not None:
                slippage = slip_factor * curr_atr
                if fill_mode == 'wick_touch':
                    raw_entry = trigger_price
                else:
                    raw_entry = closes[i]

                if direction == 'long':
                    pos_entry_price = raw_entry + slippage
                else:
                    pos_entry_price = raw_entry - slippage

                pos_stop_loss = atr_exit.initialize_stop(pos_entry_price, direction, curr_atr, ratchet_trigger)
                pos_lot_size = calculate_risk_position_size(current_balance, risk_pct, pos_entry_price, pos_stop_loss)

                if pos_lot_size > 0:
                    in_position = True
                    pos_direction = direction
                    pos_entry_bar = i

        else:
            updated_stop = atr_exit.update_ratchet(
                highs[i], lows[i], closes[i], pos_direction, curr_atr, pos_entry_price, ratchet_trigger
            )
            pos_stop_loss = updated_stop

            is_stopped = False
            exit_price = 0.0
            
            if pos_direction == 'long' and lows[i] <= pos_stop_loss:
                is_stopped = True
                exit_price = pos_stop_loss - (slip_factor * curr_atr)
            elif pos_direction == 'short' and highs[i] >= pos_stop_loss:
                is_stopped = True
                exit_price = pos_stop_loss + (slip_factor * curr_atr)

            if is_stopped:
                bars_held = i - pos_entry_bar
                
                if pos_direction == 'long':
                    pnl_raw = (exit_price - pos_entry_price) * pos_lot_size
                else:
                    pnl_raw = (pos_entry_price - exit_price) * pos_lot_size

                notional = (pos_entry_price + exit_price) * 0.5 * pos_lot_size
                comm_cost = notional * comm_rate * 2.0
                
                funding_cycles = bars_held / 32.0 if use_funding else 0.0
                funding_cost = notional * funding_8h * funding_cycles

                net_pnl = pnl_raw - comm_cost - funding_cost
                r_multiple = net_pnl / (current_balance * risk_pct) if risk_pct > 0 else 0.0
                
                current_balance += net_pnl
                
                trade_record = {
                    'entry_bar': pos_entry_bar,
                    'exit_bar': i,
                    'bars_held': bars_held,
                    'direction': pos_direction,
                    'entry_price': pos_entry_price,
                    'exit_price': exit_price,
                    'lot_size': pos_lot_size,
                    'gross_pnl': pnl_raw,
                    'comm_cost': comm_cost,
                    'funding_cost': funding_cost,
                    'net_pnl': net_pnl,
                    'r_multiple': r_multiple,
                    'balance_after': current_balance
                }
                trades.append(trade_record)

                in_position = False
                pos_direction = None
                atr_exit = ATRRatchetExit(multiplier=ratchet_mult)

        equity_curve[i] = current_balance

    return trades, equity_curve
