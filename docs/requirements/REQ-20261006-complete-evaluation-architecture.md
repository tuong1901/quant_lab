# Requirement Specification (REQ)

- **ID**: REQ-20261006-complete-evaluation-architecture
- **Title**: Complete evaluation architecture with immutable trade ledger and WFO reports
- **Created Date**: 2026-10-06
- **Status**: In Progress

## 1. Objective

Create one correct evaluation contract for strict backtests: immutable execution/trade/cash-flow evidence first, pure metric calculators second, and terminal/file reporting last. No metric may infer cash flows or completed trades from unrelated portfolio snapshots.

## 2. Architecture

```text
Dataset -> Loader -> Strategy -> Execution/Portfolio
                                  |
                                  +-> BacktestResult
                                      - equity snapshots
                                      - fills
                                      - TradeLedger (round trips)
                                      - CashFlowLedger (external funding only, if enabled)
                                      - RunMetadata (dataset hash/range/config)
                                  |
                                  v
                           EvaluationBundle (pure)
                              - Accounting
                              - Trade metrics
                              - Equity/risk metrics
                              - Cost attribution
                              - WFO/OOS + fill robustness + alpha decay
                                  |
                                  v
                           TerminalSummary + JSON/Markdown/CSV reports
```

## 3. Contracts

1. `TradeLedger` is created from fills by the trading layer. A completed trade has entry/exit times/prices, side, quantity, gross PnL, fees, funding, net PnL, R multiple, holding bars, MAE and MFE. Partial closes and reversals create deterministic close records.
2. `CashFlowLedger` records only external deposits/withdrawals. It is absent for the current no-recapitalization mode. Trading return never includes external cash flow.
3. `EvaluationBundle` contains all metric families and is generated from immutable result/ledgers:
   - accounting: initial/final equity, realized/unrealized, fees/funding, reconciliation;
   - trade: count, win rate, gross profit/loss, profit factor, expectancy, payoff, streaks, holding time, MAE/MFE, R distribution;
   - equity/risk: net/economic PnL, return, CAGR, drawdown depth/duration, volatility, Sharpe, Sortino, Calmar, recovery/ulcer;
   - cost: gross-to-net bridge, commission/funding/slippage impact;
   - research/WFO: IS/OOS windows, parameter log, fill survival, time/trade alpha decay, verdict.
4. A terminal depletion result is a structured `RunTermination`, not an exception-only string: start/end, bars, orders/fills, account state, reason, and available metrics until termination.
5. WFO/report runner must use strict DatasetLoader before splitting and must produce a report even for zero trades or account termination.

## 4. Implementation Phases

1. Add immutable `TradeLedger` and extend `BacktestResult`; cover open/add/reduce/close/reversal lifecycle.
2. Add pure trade/cost metric calculators and `EvaluationBundle`; keep existing basic/risk API compatible.
3. Add structured termination result and report partial-run semantics.
4. Extract WFO orchestration from `run_pipeline.py` into reusable strict evaluation service.
5. Make `run_backtest.py` load YAML, run strict backtest + optional WFO bundle, then write JSON/Markdown/CSV and a compact terminal summary.
6. Add P0 contract, mutation, golden and E2E tests for every ledger boundary.

## 5. Non-Negotiable Invariants

- T+1 fills and deterministic timestamp/sequence ordering.
- No lookahead; evaluation is downstream and pure.
- Fees/funding/slippage enter metrics exactly once.
- Deposits/withdrawals never appear as trading profit.
- A liquidation/termination must retain all evidence up to the exact stopping event.
- WFO train/test boundaries and embargo remain visible in the report.

## 6. Files TO Modify (implementation phase)

- [x] `src/trading/portfolio/` (trade lifecycle ledger)
- [x] `src/trading/backtest.py`
- [x] `src/evaluation/metrics.py`
- [ ] `src/evaluation/reporting.py`
- [ ] `src/evaluation/alpha_decay.py`
- [ ] `src/experiments/` (WFO orchestration service)
- [ ] `run_backtest.py`
- [ ] `run_pipeline.py`
- [ ] `config/backtest.yaml`
- [ ] tests for trade ledger, bundle, WFO, termination, and E2E

## 7. Result

- Status: In progress. Phase 1 trade ledger is implemented: open/add/reduce/close/reversal create deterministic immutable `ClosedTrade` evidence, and `BacktestResult.closed_trades` transports it downstream. Basic trade count/win rate now read this evidence; `TradeMetrics` adds net PnL, gross profit/loss, profit factor, expectancy and holding-bar support.
- Verification: `tests.portfolio.test_portfolio_contracts` + `tests.evaluation.test_metrics`: 20 passed. The legacy timing suite remains blocked before its assertions by an invalid legacy dataset storage format; an unrelated legacy result test expects a missing `BacktestResult.final_cash` property.
