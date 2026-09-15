# Pipeline Quant Lab: Detailed Execution & Evaluation Report

- **Final Verdict**: **[FAIL]**
- **Reasons**:
  - OOS Sharpe Ratio (-4.12) below minimum threshold 0.80.

## Summary Performance Telemetry

| Metric | Value |
| :--- | :--- |
| **Total OOS Trades** | 201 |
| **Win Rate** | 30.85% |
| **Expectancy / Trade** | $-27.23 |
| **Average R-Multiple** | -0.31 R |
| **Total Net PnL** | $-5473.98 |
| **Gross PnL** | $-3566.73 |
| **Commission Paid** | $1632.90 |
| **Funding Paid** | $274.35 |
| **Fee & Funding Drag** | 100.00% |
| **OOS Sharpe Ratio** | -4.12 |
| **Fill Survival Ratio** | 0.00% |

## Parameter Stability Log (Walk-Forward Windows)

|   window | preset               |   buffer_k |   lookback |   extension_ratio |   timeout | trigger_type   | ratchet_trigger   |
|---------:|:---------------------|-----------:|-----------:|------------------:|----------:|:---------------|:------------------|
|        0 | tier1_plus_extension |       0.55 |         45 |               0.8 |        12 | engulfing      | at_2R             |
|        1 | tier1_plus_extension |       0.5  |         85 |               0.5 |        44 | engulfing      | at_2R             |