"""
Reporting & Evaluation Engine for M15 BTCUSDT Pipeline Quant Lab.
Generates OOS Equity Curve telemetry, Parameter Stability Logs, Dual-Fill Comparisons,
Fee Drag Ratios, and determines final PASS / WARN / FAIL system verdict.
Automatically saves report artifacts to the reports/ directory.
"""

import os
import json
from typing import List, Dict, Any
import numpy as np
import pandas as pd


def generate_pipeline_report(
    wfo_results: List[Dict[str, Any]],
    alpha_decay_summary: Dict[str, Any],
    fill_comparison: Dict[str, Any],
    output_dir: str = "reports"
) -> Dict[str, Any]:
    """
    [PURPOSE]: Compile full backtest lab evaluation metrics into a comprehensive structured report
               and export artifacts (Markdown, JSON, CSVs) into output_dir.
    [DEPENDENCIES]: Called at pipeline completion by run_pipeline.py.
    [ARGS]: wfo_results — Results across all Walk-Forward OOS windows.
            alpha_decay_summary — Dual-axis alpha decay telemetry dictionary.
            fill_comparison — Comparative results between Wick Touch and Bar Close fills.
            output_dir — Folder path to write report artifacts to (default "reports").
    [RETURNS]: Dict — Full report data structure.
    [SIDE EFFECTS]: Creates directory output_dir and writes file artifacts to disk.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    all_oos_trades = []
    for window in wfo_results:
        all_oos_trades.extend(window.get('oos_trades', []))

    n_trades = len(all_oos_trades)
    if n_trades == 0:
        report = {
            'verdict': 'FAIL',
            'verdict_reasons': ['Zero OOS trades generated across all walk-forward windows.'],
            'summary_metrics': {}
        }
        _save_reports_to_disk(report, all_oos_trades, wfo_results, output_dir)
        return report

    net_pnls = [t['net_pnl'] for t in all_oos_trades]
    gross_pnls = [t['gross_pnl'] for t in all_oos_trades]
    comm_costs = [t['comm_cost'] for t in all_oos_trades]
    funding_costs = [t['funding_cost'] for t in all_oos_trades]
    r_multiples = [t['r_multiple'] for t in all_oos_trades]
    wins = [t for t in all_oos_trades if t['net_pnl'] > 0]

    tot_net_pnl = sum(net_pnls)
    tot_gross_pnl = sum(gross_pnls)
    tot_comm = sum(comm_costs)
    tot_funding = sum(funding_costs)
    tot_friction = tot_comm + tot_funding

    win_rate = len(wins) / float(n_trades)
    expectancy = tot_net_pnl / float(n_trades)
    avg_r = np.mean(r_multiples)
    fee_drag_ratio = (tot_friction / max(1e-4, tot_gross_pnl)) if tot_gross_pnl > 0 else 1.0

    equity_series = [10000.0]
    for t in all_oos_trades:
        equity_series.append(t['balance_after'])
    returns = np.diff(equity_series) / equity_series[:-1]
    std_ret = np.std(returns)
    oos_sharpe = (np.mean(returns) / max(1e-9, std_ret)) * np.sqrt(35040) if len(returns) > 1 else 0.0

    param_log = []
    for w in wfo_results:
        param_log.append({
            'window': w.get('window_idx'),
            'preset': w.get('best_params', {}).get('zone_preset'),
            'buffer_k': w.get('best_params', {}).get('zone_buffer_k'),
            'lookback': w.get('best_params', {}).get('swing_lookback'),
            'extension_ratio': w.get('best_params', {}).get('projection_extension_ratio'),
            'timeout': w.get('best_params', {}).get('stage_timeout_bars'),
            'trigger_type': w.get('best_params', {}).get('trigger_candle_type'),
            'ratchet_trigger': w.get('best_params', {}).get('ratchet_activation_trigger')
        })

    wick_pnl = fill_comparison.get('wick_touch_pnl', 0.0)
    close_pnl = fill_comparison.get('bar_close_pnl', 0.0)
    fill_survival_ratio = (close_pnl / max(1e-4, wick_pnl)) if wick_pnl > 0 else 0.0

    verdict = 'PASS'
    verdict_reasons = []

    if fill_survival_ratio < 0.40 and wick_pnl > 0:
        verdict = 'FAIL'
        verdict_reasons.append("System relies strictly on optimistic Wick Touch fills (fails under Bar Close fills).")
    elif oos_sharpe < 0.8:
        verdict = 'FAIL'
        verdict_reasons.append(f"OOS Sharpe Ratio ({oos_sharpe:.2f}) below minimum threshold 0.80.")
    elif fee_drag_ratio > 0.50:
        verdict = 'FAIL'
        verdict_reasons.append(f"Fee Drag Ratio ({fee_drag_ratio*100:.1f}%) exceeds 50% threshold.")
    elif oos_sharpe < 1.2 or fee_drag_ratio > 0.35:
        verdict = 'WARN'
        verdict_reasons.append("Sub-optimal Sharpe or moderate fee drag ratio.")
    else:
        verdict_reasons.append("Robust Walk-Forward Sharpe, healthy fill survival, and manageable fee drag.")

    report = {
        'verdict': verdict,
        'verdict_reasons': verdict_reasons,
        'summary_metrics': {
            'total_oos_trades': n_trades,
            'win_rate': float(win_rate),
            'expectancy_per_trade': float(expectancy),
            'avg_r_multiple': float(avg_r),
            'total_net_pnl': float(tot_net_pnl),
            'total_gross_pnl': float(tot_gross_pnl),
            'total_commission_paid': float(tot_comm),
            'total_funding_paid': float(tot_funding),
            'fee_drag_ratio': float(fee_drag_ratio),
            'oos_sharpe': float(oos_sharpe),
            'fill_survival_ratio': float(fill_survival_ratio)
        },
        'param_stability_log': param_log,
        'alpha_decay_summary': alpha_decay_summary,
        'fill_comparison': fill_comparison
    }

    _save_reports_to_disk(report, all_oos_trades, wfo_results, output_dir)
    return report


def _save_reports_to_disk(
    report: Dict[str, Any],
    all_oos_trades: List[Dict[str, Any]],
    wfo_results: List[Dict[str, Any]],
    output_dir: str
) -> None:
    """
    [PURPOSE]: Export JSON, Markdown, and CSV telemetry reports into output_dir.
    [DEPENDENCIES]: Called by generate_pipeline_report().
    [ARGS]: report — Dict report output.
            all_oos_trades — List of trade records.
            wfo_results — WFO results list.
            output_dir — Target output folder path.
    [RETURNS]: None.
    [SIDE EFFECTS]: Writes files to disk.
    """
    # 1. Save JSON report
    json_path = os.path.join(output_dir, "pipeline_report.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    # 2. Save Markdown report
    md_path = os.path.join(output_dir, "pipeline_report.md")
    m = report.get('summary_metrics', {})
    md_content = f"""# Pipeline Quant Lab: Detailed Execution & Evaluation Report

- **Final Verdict**: **[{report.get('verdict', 'N/A')}]**
- **Reasons**:
"""
    for r in report.get('verdict_reasons', []):
        md_content += f"  - {r}\n"

    md_content += f"""
## Summary Performance Telemetry

| Metric | Value |
| :--- | :--- |
| **Total OOS Trades** | {m.get('total_oos_trades', 0)} |
| **Win Rate** | {m.get('win_rate', 0.0)*100:.2f}% |
| **Expectancy / Trade** | ${m.get('expectancy_per_trade', 0.0):.2f} |
| **Average R-Multiple** | {m.get('avg_r_multiple', 0.0):.2f} R |
| **Total Net PnL** | ${m.get('total_net_pnl', 0.0):.2f} |
| **Gross PnL** | ${m.get('total_gross_pnl', 0.0):.2f} |
| **Commission Paid** | ${m.get('total_commission_paid', 0.0):.2f} |
| **Funding Paid** | ${m.get('total_funding_paid', 0.0):.2f} |
| **Fee & Funding Drag** | {m.get('fee_drag_ratio', 0.0)*100:.2f}% |
| **OOS Sharpe Ratio** | {m.get('oos_sharpe', 0.0):.2f} |
| **Fill Survival Ratio** | {m.get('fill_survival_ratio', 0.0)*100:.2f}% |

## Parameter Stability Log (Walk-Forward Windows)

"""
    p_log = report.get('param_stability_log', [])
    if p_log:
        df_p = pd.DataFrame(p_log)
        md_content += df_p.to_markdown(index=False)
    else:
        md_content += "No WFO parameter log recorded.\n"

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 3. Save OOS Equity Curve CSV
    if all_oos_trades:
        df_trades = pd.DataFrame(all_oos_trades)
        df_trades.to_csv(os.path.join(output_dir, "oos_trades.csv"), index=False)

    # 4. Save WFO Parameter Stability Log CSV
    if p_log:
        df_p = pd.DataFrame(p_log)
        df_p.to_csv(os.path.join(output_dir, "wfo_parameter_log.csv"), index=False)
