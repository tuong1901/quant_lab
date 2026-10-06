# Portfolio contract tests

`test_portfolio_contracts.py` verifies P0 ledger invariants using synthetic `Fill` objects only. It covers position lifecycle, PnL, fees, mark-to-market, equity reconciliation, duplicate-fill protection, and one golden lifecycle sequence.

P1 work—margin policy, RiskManager integration, funding scheduling, and multi-symbol isolation—is deliberately outside this suite's current scope.
