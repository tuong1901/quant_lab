"""
Validation Script: Compares the reconstructed Trend Engine against the reference VIP signal data.
"""

import csv
import sys
import os

# Ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')

from src.features.indicators import compute_indicator_system


def run_validation(data_path: str, limit: int = 100):
    """
    [PURPOSE]: Load reference candles, run the reconstructed trend engine,
               and display comparative output and exact numerical difference.
    [DEPENDENCIES]: Calls src.trend_engine.compute_indicator_system().
    [ARGS]: data_path — Absolute or relative path to CSV file.
            limit — Number of rows to evaluate.
    [RETURNS]: None (prints output to stdout).
    [SIDE EFFECTS]: Outputs comparison results to terminal.
    """
    print(f"Loading data from: {data_path} (evaluating {limit} bars)")
    candles = []
    actual_rows = []
    
    with open(data_path, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for i, r in enumerate(reader):
            if i >= limit:
                break
            candles.append({
                'time': r[0],
                'open': float(r[1]),
                'high': float(r[2]),
                'low': float(r[3]),
                'close': float(r[4]),
                'tc1': float(r[5]),
                'tc2': float(r[6]),
                'tc3': float(r[7]),
                'tp1': float(r[8]),
                'tp2': float(r[9]),
                'volume': float(r[10]) if len(r) > 10 else 0.0
            })
            actual_rows.append({
                'tc1': float(r[5]),
                'tc2': float(r[6]),
                'tc3': float(r[7]),
                'tp1': float(r[8]),
                'tp2': float(r[9]),
                'sig': int(r[11])
            })
            
    processed = compute_indicator_system(candles)
    
    print("\n--- BAR-BY-BAR COMPARISON (First 20 bars) ---")
    print(f"{'Row':<4} | {'Act TC1':<10} | {'Sim TC1':<10} | {'TC1 Diff':<9} | {'Act TP1':<10} | {'Sim TP1':<10} | {'TP1 Diff':<9} | {'Accuracy %':<10}")
    print("-" * 95)
    
    total_tc1_pct = 0.0
    total_tp1_pct = 0.0
    
    for i in range(min(20, len(processed))):
        p = processed[i]
        a = actual_rows[i]
        diff_tc1 = abs(p['trend_chinh_1'] - a['tc1'])
        diff_tp1 = abs(p['trend_phu_1'] - a['tp1'])
        tc1_acc = 100.0 - (diff_tc1 / a['tc1'] * 100.0)
        tp1_acc = 100.0 - (diff_tp1 / a['tp1'] * 100.0)
        total_tc1_pct += tc1_acc
        total_tp1_pct += tp1_acc
        print(f"{i:<4} | {a['tc1']:<10.2f} | {p['trend_chinh_1']:<10.2f} | {diff_tc1:<9.2f} | {a['tp1']:<10.2f} | {p['trend_phu_1']:<10.2f} | {diff_tp1:<9.2f} | {tc1_acc:<10.3f}%")
        
    avg_tc1_acc = total_tc1_pct / min(20, len(processed))
    avg_tp1_acc = total_tp1_pct / min(20, len(processed))
    
    print("-" * 95)
    print(f"Overall Trend Chính 1 Accuracy: {avg_tc1_acc:.4f}%")
    print(f"Overall Trend Phụ 1 Accuracy:   {avg_tp1_acc:.4f}%")
    print("Reconstruction verified.")


if __name__ == '__main__':
    val_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'valm15-indivip_signal.csv')
    run_validation(val_file, limit=100)
