"""
[PURPOSE]: Optuna Bayesian Optimizer & Plateau Champion Engine (`src/engine/optimizer.py`).
[DEPENDENCIES]: numpy, optuna, src.engine.simulator.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import optuna
from optuna.samplers import TPESampler

from src.engine.simulator import run_trade_simulation

optuna.logging.set_verbosity(optuna.logging.WARNING)


def objective_function(
    trial: optuna.Trial,
    df_is: Any,
    atr_is: np.ndarray,
    swings_is: Tuple[np.ndarray, np.ndarray, np.ndarray],
    search_space: Dict[str, Any],
    fixed_config: Dict[str, Any]
) -> float:
    """
    [PURPOSE]: Optuna objective function evaluating in-sample (IS) trial performance.
    """
    params = {}
    for param_name, cfg in search_space.get('search_space', {}).items():
        p_type = cfg['type']
        if p_type == 'categorical':
            params[param_name] = trial.suggest_categorical(param_name, cfg['choices'])
        elif p_type == 'float':
            params[param_name] = trial.suggest_float(param_name, cfg['low'], cfg['high'], step=cfg.get('step'))
        elif p_type == 'int':
            params[param_name] = trial.suggest_int(param_name, cfg['low'], cfg['high'], step=cfg.get('step'))

    trades, eq_curve = run_trade_simulation(
        df_is, atr_is, swings_is, params, fixed_config, fill_mode='bar_close'
    )
    
    if len(trades) < 50:
        return -999.0
        
    returns = np.diff(eq_curve) / eq_curve[:-1]
    std_ret = np.std(returns)
    if std_ret <= 1e-9:
        return -999.0
        
    sharpe = (np.mean(returns) / std_ret) * np.sqrt(35040)
    return float(sharpe)


def evaluate_plateau_champion(
    top_params: Dict[str, Any],
    df_is: Any,
    atr_is: np.ndarray,
    swings_is: Tuple[np.ndarray, np.ndarray, np.ndarray],
    search_space: Dict[str, Any],
    fixed_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    [PURPOSE]: Perform epsilon-neighborhood perturbation check around top trial parameters.
    """
    base_trades, base_eq = run_trade_simulation(df_is, atr_is, swings_is, top_params, fixed_config)
    if len(base_trades) < 50:
        return top_params
        
    base_ret = np.diff(base_eq) / base_eq[:-1]
    base_sharpe = (np.mean(base_ret) / max(1e-9, np.std(base_ret))) * np.sqrt(35040)

    neighborhood_scores = [base_sharpe]
    for key, val in top_params.items():
        if isinstance(val, float):
            for delta in [-0.10, 0.10]:
                perturbed = dict(top_params)
                perturbed[key] = max(0.01, val * (1.0 + delta))
                tr, eq = run_trade_simulation(df_is, atr_is, swings_is, perturbed, fixed_config)
                if len(tr) >= 30:
                    r = np.diff(eq) / eq[:-1]
                    sh = (np.mean(r) / max(1e-9, np.std(r))) * np.sqrt(35040)
                    neighborhood_scores.append(sh)

    plateau_score = np.mean(neighborhood_scores)
    top_params['_plateau_score'] = float(plateau_score)
    top_params['_is_sharpe'] = float(base_sharpe)
    return top_params


def run_optuna_study(
    df_is: Any,
    atr_is: np.ndarray,
    swings_is: Tuple[np.ndarray, np.ndarray, np.ndarray],
    search_space: Dict[str, Any],
    fixed_config: Dict[str, Any],
    n_trials: int = 100
) -> Dict[str, Any]:
    """
    [PURPOSE]: Execute Optuna Bayesian optimization study for a single WFO window.
    """
    sampler = TPESampler(seed=42)
    study = optuna.create_study(direction='maximize', sampler=sampler)
    
    study.optimize(
        lambda trial: objective_function(trial, df_is, atr_is, swings_is, search_space, fixed_config),
        n_trials=n_trials,
        show_progress_bar=False
    )
    
    best_params = study.best_params
    champion_params = evaluate_plateau_champion(
        best_params, df_is, atr_is, swings_is, search_space, fixed_config
    )
    
    return champion_params
