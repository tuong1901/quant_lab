"""
CLI Entry Point for Pipeline Quant Lab: Fibo Zone-Registry + Projection + ATR Ratchet (M15 BTCUSDT).
Orchestrates config loading, causal feature generation, single-window speed benchmarking,
Purged Walk-Forward Optimization, dual-fill execution simulation, reporting artifact export,
and Golden Behavioral Baseline verification.
"""

import os
import sys
import time
import json
import argparse
import yaml
import numpy as np
import pandas as pd

from src.data.loader import load_m15_ohlcv
from src.features.indicators import calculate_causal_atr, calculate_causal_swings
from src.experiments.splitter import PurgedWFOSplitter
from src.engine.backtest.optimizer import run_optuna_study
from src.engine.backtest.simulator import run_trade_simulation
from src.evaluation.alpha_decay import (
    evaluate_time_horizons,
    evaluate_trade_count_horizons,
    compute_alpha_decay_summary,
)
from src.evaluation.reporting import generate_pipeline_report


def parse_args():
    """
    [PURPOSE]: Parse command-line arguments for pipeline execution.
    """
    parser = argparse.ArgumentParser(description="Pipeline Quant Lab: Fibo Zone-Registry + ATR Ratchet")
    parser.add_argument('--dataset', type=str, default='data/m15-indivip_signal.csv', help="Path to M15 CSV dataset")
    parser.add_argument('--benchmark-trials', type=int, default=None, help="Run single-window execution benchmark with N trials")
    parser.add_argument('--n-trials', type=int, default=50, help="Optuna trials per WFO window")
    parser.add_argument('--n-windows', type=int, default=3, help="Number of Purged WFO windows")
    parser.add_argument('--reports-dir', type=str, default='reports', help="Directory to save output reports")
    parser.add_argument('--verify-golden-baseline', type=str, default=None, help="Path to golden baseline JSON file for numerical verification")
    return parser.parse_args()


def load_all_configs():
    """
    [PURPOSE]: Load zones.yaml, fixed_params.yaml, and search_space.yaml into memory.
    """
    with open('config/zones.yaml', 'r', encoding='utf-8') as f:
        zones_cfg = yaml.safe_load(f)
    with open('config/fixed_params.yaml', 'r', encoding='utf-8') as f:
        fixed_cfg = yaml.safe_load(f)
    with open('config/search_space.yaml', 'r', encoding='utf-8') as f:
        space_cfg = yaml.safe_load(f)
        
    return zones_cfg, fixed_cfg, space_cfg


def verify_golden_baseline(golden_path: str) -> bool:
    """
    [PURPOSE]: Verify that new SSOT implementation produces 100.0000% exact numerical match against golden baseline.
    """
    if not os.path.exists(golden_path):
        print(f"[GOLDEN VERIFICATION ERROR] File not found: {golden_path}")
        return False

    with open(golden_path, 'r', encoding='utf-8') as f:
        golden_data = json.load(f)

    dataset_path = golden_data['dataset']
    print(f"[GOLDEN VERIFICATION] Loading dataset: {dataset_path}...")
    df = load_m15_ohlcv(dataset_path)

    zones_cfg, fixed_cfg, space_cfg = load_all_configs()
    atr_period = fixed_cfg.get('atr_ratchet', {}).get('period', 14)
    atr_series = calculate_causal_atr(df, period=atr_period)
    swings = calculate_causal_swings(df, lookback=20)

    n_bars = golden_data['bars_evaluated']
    df_slice = df.iloc[:n_bars].copy()
    atr_slice = atr_series[:n_bars]
    swings_slice = (swings[0][:n_bars], swings[1][:n_bars], swings[2][:n_bars])

    champion_params = golden_data['champion_params']

    trades, equity = run_trade_simulation(
        df_slice, atr_slice, swings_slice, champion_params, fixed_cfg, fill_mode='bar_close'
    )

    expected_trades = golden_data['trades']
    expected_equity = golden_data['equity_curve']

    if len(trades) != len(expected_trades):
        print(f"[GOLDEN VERIFICATION FAILED] Trade count mismatch: got {len(trades)}, expected {len(expected_trades)}")
        return False

    mismatches = 0
    for i in range(len(trades)):
        actual = trades[i]
        exp = expected_trades[i]
        diff_pnl = abs(actual['net_pnl'] - exp['net_pnl'])
        if diff_pnl > 1e-6:
            print(f"   Mismatch at trade {i}: actual net_pnl={actual['net_pnl']:.6f}, expected={exp['net_pnl']:.6f}")
            mismatches += 1

    final_eq_diff = abs(equity[-1] - golden_data['final_equity'])
    if final_eq_diff > 1e-6:
        print(f"[GOLDEN VERIFICATION FAILED] Final equity mismatch: actual={equity[-1]:.6f}, expected={golden_data['final_equity']:.6f}")
        return False

    if mismatches == 0:
        print("================================================================================")
        print("GOLDEN BEHAVIORAL BASELINE VERIFICATION: PASSED 100.0000% NUMERICAL MATCH!")
        print(f" - Total Trades Evaluated: {len(trades)}")
        print(f" - Final Equity Exact Match: ${equity[-1]:.2f}")
        print("================================================================================")
        return True
    else:
        print(f"[GOLDEN VERIFICATION FAILED] Found {mismatches} trade PnL mismatches.")
        return False


def main():
    args = parse_args()

    if args.verify_golden_baseline:
        success = verify_golden_baseline(args.verify_golden_baseline)
        if not success:
            sys.exit(1)
        return

    print("================================================================================")
    print("PIPELINE QUANT LAB: FIBO ZONE-REGISTRY + PROJECTION + ATR RATCHET (M15 BTCUSDT)")
    print("================================================================================")

    zones_cfg, fixed_cfg, space_cfg = load_all_configs()
    
    csv_path = args.dataset
    if not os.path.exists(csv_path):
        print(f"Dataset path '{csv_path}' not found. Exiting.")
        sys.exit(1)

    print(f"[1/5] Loading M15 Dataset: {csv_path}...")
    df = load_m15_ohlcv(csv_path)
    print(f"      Total Bars Loaded: {len(df):,}")

    atr_period = fixed_cfg.get('atr_ratchet', {}).get('period', 14)
    print(f"[2/5] Computing Causal Wilder RMA ATR (period={atr_period})...")
    atr_series = calculate_causal_atr(df, period=atr_period)

    print("[3/5] Computing Causal Swing Engine (lookback=20)...")
    swings = calculate_causal_swings(df, lookback=20)

    if args.benchmark_trials is not None:
        n_bench = args.benchmark_trials
        print(f"\n[BENCHMARK MODE] Running speed test with {n_bench} trials on first 50,000 bars...")
        df_bench = df.iloc[:min(len(df), 50000)].copy()
        n_b = len(df_bench)
        atr_bench = atr_series[:n_b]
        swings_bench = (swings[0][:n_b], swings[1][:n_b], swings[2][:n_b])

        t0 = time.time()
        best_champion = run_optuna_study(
            df_bench, atr_bench, swings_bench, space_cfg, fixed_cfg, n_trials=n_bench
        )
        elapsed = time.time() - t0
        sec_per_trial = elapsed / float(n_bench)
        
        print("--------------------------------------------------------------------------------")
        print(f"BENCHMARK COMPLETED: {n_bench} trials executed in {elapsed:.2f} seconds ({sec_per_trial*1000:.1f} ms/trial)")
        print(f"Best Champion Parameters Found: {best_champion}")
        print("--------------------------------------------------------------------------------")
        return

    print(f"\n[4/5] Running Purged Walk-Forward Optimization ({args.n_windows} windows, {args.n_trials} trials/window)...")
    splitter = PurgedWFOSplitter(min_is_trades=300, embargo_bars=96, n_windows=args.n_windows)
    splits = splitter.generate_splits(len(df))

    wfo_results = []
    full_oos_trades = []

    for split in splits:
        w_idx = split['window_idx']
        tr_s, tr_e = split['train_start'], split['train_end']
        te_s, te_e = split['test_start'], split['test_end']

        print(f"   --> Window {w_idx+1}/{len(splits)} | Train: bars {tr_s:,}-{tr_e:,} | Test: bars {te_s:,}-{te_e:,}")

        df_is = df.iloc[tr_s:tr_e].copy()
        atr_is = atr_series[tr_s:tr_e]
        swings_is = (swings[0][tr_s:tr_e], swings[1][tr_s:tr_e], swings[2][tr_s:tr_e])

        champion_params = run_optuna_study(
            df_is, atr_is, swings_is, space_cfg, fixed_cfg, n_trials=args.n_trials
        )

        df_oos = df.iloc[te_s:te_e].copy()
        atr_oos = atr_series[te_s:te_e]
        swings_oos = (swings[0][te_s:te_e], swings[1][te_s:te_e], swings[2][te_s:te_e])

        oos_trades, oos_eq = run_trade_simulation(
            df_oos, atr_oos, swings_oos, champion_params, fixed_cfg, fill_mode='bar_close'
        )

        wfo_results.append({
            'window_idx': w_idx,
            'best_params': champion_params,
            'oos_trades': oos_trades,
            'oos_equity': oos_eq
        })
        full_oos_trades.extend(oos_trades)

    print("\n[5/5] Running Dual-Fill Execution Comparison & Alpha Decay Analysis...")
    last_params = wfo_results[-1]['best_params'] if wfo_results else {}
    
    wick_trades, _ = run_trade_simulation(df, atr_series, swings, last_params, fixed_cfg, fill_mode='wick_touch')
    close_trades, _ = run_trade_simulation(df, atr_series, swings, last_params, fixed_cfg, fill_mode='bar_close')

    wick_pnl = sum([t['net_pnl'] for t in wick_trades])
    close_pnl = sum([t['net_pnl'] for t in close_trades])
    fill_comparison = {
        'wick_touch_trades': len(wick_trades),
        'wick_touch_pnl': float(wick_pnl),
        'bar_close_trades': len(close_trades),
        'bar_close_pnl': float(close_pnl)
    }

    time_decay = evaluate_time_horizons(df, atr_series, swings, last_params, fixed_cfg)
    trade_decay = evaluate_trade_count_horizons(full_oos_trades)
    alpha_summary = compute_alpha_decay_summary(time_decay, trade_decay)

    reports_dir = args.reports_dir
    report = generate_pipeline_report(wfo_results, alpha_summary, fill_comparison, output_dir=reports_dir)

    print("\n================================================================================")
    print(f"LAB VERDICT: [{report['verdict']}]")
    print("================================================================================")
    for reason in report.get('verdict_reasons', []):
        print(f" - {reason}")

    metrics = report.get('summary_metrics', {})
    print("\nSUMMARY PERFORMANCE METRICS:")
    print(f" - Total OOS Trades:       {metrics.get('total_oos_trades', 0)}")
    print(f" - Win Rate:               {metrics.get('win_rate', 0.0)*100:.2f}%")
    print(f" - Expectancy / Trade:     ${metrics.get('expectancy_per_trade', 0.0):.2f}")
    print(f" - Average R-Multiple:     {metrics.get('avg_r_multiple', 0.0):.2f} R")
    print(f" - Total Net PnL:          ${metrics.get('total_net_pnl', 0.0):.2f}")
    print(f" - Fee & Funding Drag:     {metrics.get('fee_drag_ratio', 0.0)*100:.2f}%")
    print(f" - OOS Sharpe Ratio:       {metrics.get('oos_sharpe', 0.0):.2f}")
    print(f" - Fill Survival Ratio:    {metrics.get('fill_survival_ratio', 0.0)*100:.2f}%")
    print("--------------------------------------------------------------------------------")
    print(f"REPORTS EXPORTED TO DIR: [ {os.path.abspath(reports_dir)} ]")
    print(f" - Markdown Report:  {os.path.join(reports_dir, 'pipeline_report.md')}")
    print(f" - JSON Report:      {os.path.join(reports_dir, 'pipeline_report.json')}")
    print(f" - OOS Trades CSV:   {os.path.join(reports_dir, 'oos_trades.csv')}")
    print(f" - WFO Param Log:    {os.path.join(reports_dir, 'wfo_parameter_log.csv')}")
    print("================================================================================")


if __name__ == '__main__':
    main()
