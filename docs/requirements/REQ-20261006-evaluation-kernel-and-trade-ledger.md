# Requirement Specification (REQ)

- **ID**: REQ-20261006-evaluation-kernel-and-trade-ledger
- **Title**: Xây Evaluation Kernel theo equity curve và Trade Ledger
- **Created Date**: 2026-10-06
- **Status**: In Progress — Phase A

---

## 1. Overview & Objective
Tách evaluation thành hai nguồn sự thật: equity-curve metrics lấy từ `BacktestResult`, và trade metrics lấy từ `TradeLedger`. Loại bỏ việc suy diễn trade statistics từ chênh lệch `realized_pnl` snapshot vì partial close/reversal không phải round-trip trade record.

## 2. Scope & Target Architectural Layer
**Phase A (P0, implement first):** equity Performance/Risk kernel: net return, CAGR, max drawdown $, max drawdown %, drawdown duration, annualized volatility, Sharpe, Sortino, Calmar; annualization nhận `Timeframe`, không hard-code M15.

**Phase B (design then implement separately):** immutable `TradeRecord`/`TradeLedger`, round-trip trade statistics, gross-to-net cost attribution, planned RR/R-multiple, and accounting reconciliation. MAE/MFE requires bar traversal while a trade is open and is excluded until the ledger contract exists.

WFO, alpha decay, model-classification metrics, Monte Carlo, stress testing, and report redesign are out of scope for this REQ.

## 3. Decisions Required Before Implementation
1. Invalid CAGR inputs (`duration <= 0`, `initial <= 0`, `final <= 0`): recommended policy is raise `InvalidEvaluationError`.
2. Undefined ratios (zero return volatility, zero downside deviation, zero max drawdown): recommended policy is `None`, never infinity or silent zero.
3. Risk-free rate: recommended default `0.0`, passed explicitly as an annual decimal rate.
4. `TradeLedger` ownership: recommended owner is `src/trading`, built from fills/position lifecycle; `src/evaluation` reads it only.

## 4. Detailed Approach & Steps
1. Create pure equity-curve input/value objects and Performance/Risk metric result container.
2. Implement timeframe-aware annualization for crypto 24/7: M15=35040, H1=8760, H4=2190, D1=365.
3. Implement and golden-test return, CAGR, drawdown, volatility, Sharpe, Sortino, and Calmar, including all undefined/invalid edge cases.
4. Keep `BasicMetrics` compatibility API but stop using snapshot PnL deltas as the authoritative source for future round-trip trade statistics.
5. Write a separate follow-up REQ for TradeRecord/TradeLedger wiring once its producer contract is approved.

## 5. Files TO Modify
- [x] `src/evaluation/metrics.py`
- [x] `src/evaluation/__init__.py`
- [x] `src/evaluation/README.md`
- [x] `tests/evaluation/test_metrics.py`
- [x] `tests/evaluation/test_equity_risk_metrics.py` (new)
- [x] `PROJECT_STATUS.md`
- [x] `docs/requirements/REQ-20261006-evaluation-kernel-and-trade-ledger.md`

## 6. Acceptance Criteria
- [x] Performance/Risk metrics have deterministic golden tests and no hard-coded M15 annualization.
- [x] Undefined ratios follow the approved explicit policy; no infinity/silent fallback.
- [x] `BasicMetrics` remains backward-compatible.
- [x] No trade-level statistic is presented as authoritative without `TradeLedger` input.
- [x] Phase B is documented but does not leak into Phase A implementation.

## 7. Verification Plan
- [x] `python -m unittest tests.evaluation.test_metrics tests.evaluation.test_equity_risk_metrics` — 13 tests passed.
- [x] Existing strict E2E remains green after metric compatibility check — passed on the approved real-data fixture.

## 8. Result
- Status: Completed — 13 unit tests and strict E2E passed.
- Date: 2026-10-06
- Phase A result: equity Performance/Risk kernel is production-compatible. TradeLedger remains a separate unimplemented Phase B contract.
- Date: 2026-10-06
