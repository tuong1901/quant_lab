"""Strict production backtest CLI: dataset to strategy, execution, and evaluation."""

import argparse
from dataclasses import dataclass
from typing import Sequence

import pandas as pd

from src.data.dataset import Dataset
from src.data.loader import DatasetLoader
from src.evaluation import (
    AccountingReconciliation,
    BasicMetrics,
    EquityRiskMetrics,
    calculate_accounting_reconciliation,
    calculate_basic_metrics,
    calculate_equity_risk_metrics,
)
from src.strategies.ema import EMAStrategy
from src.trading.backtest import BacktestEngine, BacktestResult


@dataclass(frozen=True)
class StrictBacktestEvaluation:
    """
    [PURPOSE]: Group the result and all read-only evaluation views from one strict backtest run.
    [DEPENDENCIES]: Produced by run_strict_backtest.
    [ARGS]: result — strict BacktestResult; basic, risk, accounting — evaluation views.
    [RETURNS]: Immutable complete strict backtest outcome.
    [SIDE EFFECTS]: None.
    """
    result: BacktestResult
    basic: BasicMetrics
    risk: EquityRiskMetrics
    accounting: AccountingReconciliation


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """
    [PURPOSE]: Parse strict backtest CLI options.
    [DEPENDENCIES]: argparse.
    [ARGS]: argv — Optional argument sequence for tests; None reads process arguments.
    [RETURNS]: Parsed CLI namespace.
    [SIDE EFFECTS]: Exits with argparse usage error for invalid arguments.
    """
    parser = argparse.ArgumentParser(
        description="Strict Dataset -> EMA Strategy -> BacktestEngine -> Evaluation runner"
    )
    parser.add_argument(
        "--dataset-definition",
        required=True,
        help="Path to a strict Dataset YAML descriptor.",
    )
    parser.add_argument(
        "--fast-period",
        type=int,
        default=20,
        help="Fast EMA period for the reference EMA strategy (default: 20).",
    )
    parser.add_argument(
        "--slow-period",
        type=int,
        default=50,
        help="Slow EMA period for the reference EMA strategy (default: 50).",
    )
    parser.add_argument(
        "--risk-free-rate",
        type=float,
        default=0.0,
        help="Annual decimal risk-free rate used by Sharpe and Sortino (default: 0.0).",
    )
    return parser.parse_args(argv)


def add_ema_features(frame: pd.DataFrame, fast_period: int, slow_period: int) -> pd.DataFrame:
    """
    [PURPOSE]: Add the EMA feature columns required by the reference EMA strategy.
    [DEPENDENCIES]: Called by run_strict_backtest before BacktestEngine.run.
    [ARGS]: frame — strict canonical OHLCV DataFrame; fast_period, slow_period — positive EMA spans.
    [RETURNS]: Copy of frame with ema{fast_period} and ema{slow_period} columns.
    [SIDE EFFECTS]: Raises ValueError for invalid or identical EMA periods.
    """
    if fast_period <= 0 or slow_period <= 0:
        raise ValueError("EMA periods must be strictly positive.")
    if fast_period >= slow_period:
        raise ValueError("fast_period must be smaller than slow_period.")
    featured = frame.copy()
    featured[f"ema{fast_period}"] = featured["close"].ewm(
        span=fast_period, adjust=False
    ).mean()
    featured[f"ema{slow_period}"] = featured["close"].ewm(
        span=slow_period, adjust=False
    ).mean()
    return featured


def run_strict_backtest(
    dataset_definition: str,
    fast_period: int = 20,
    slow_period: int = 50,
    risk_free_rate: float = 0.0,
) -> StrictBacktestEvaluation:
    """
    [PURPOSE]: Run the complete strict production path from Dataset YAML to evaluated backtest result.
    [DEPENDENCIES]: DatasetLoader, EMAStrategy, BacktestEngine, and evaluation public API.
    [ARGS]: dataset_definition — strict YAML path; EMA periods; annual decimal risk-free rate.
    [RETURNS]: StrictBacktestEvaluation containing result, metrics, risk, and accounting views.
    [SIDE EFFECTS]: Reads the YAML descriptor and its referenced market-data storage.
    """
    dataset = Dataset.from_yaml(dataset_definition)
    market_data = DatasetLoader().load(dataset)
    frame = add_ema_features(market_data.df, fast_period, slow_period)
    strategy = EMAStrategy(fast_period=fast_period, slow_period=slow_period)
    result = BacktestEngine(strategy=strategy).run(frame)
    basic = calculate_basic_metrics(result)
    risk = calculate_equity_risk_metrics(
        basic.equity_curve,
        timeframe=dataset.timeframe,
        risk_free_rate=risk_free_rate,
    )
    accounting = calculate_accounting_reconciliation(result)
    return StrictBacktestEvaluation(
        result=result,
        basic=basic,
        risk=risk,
        accounting=accounting,
    )


def format_evaluation(evaluation: StrictBacktestEvaluation) -> str:
    """
    [PURPOSE]: Render a complete human-readable accounting, performance, and risk summary.
    [DEPENDENCIES]: Reads StrictBacktestEvaluation only.
    [ARGS]: evaluation — Completed strict backtest outcome.
    [RETURNS]: Multi-line report string suitable for CLI output.
    [SIDE EFFECTS]: None.
    """
    basic = evaluation.basic
    risk = evaluation.risk
    accounting = evaluation.accounting
    return "\n".join(
        [
            "STRICT BACKTEST EVALUATION",
            "=" * 72,
            f"Bars processed:         {evaluation.result.bars_processed}",
            f"Signals / orders / fills:{len(evaluation.result.signals)} / {len(evaluation.result.orders)} / {len(evaluation.result.fills)}",
            "",
            "ACCOUNTING RECONCILIATION",
            f"Initial capital:         ${accounting.initial_capital:,.2f}",
            f"Realized PnL:          {accounting.realized_pnl:+,.2f}",
            f"Fees paid:              -${accounting.total_fees:,.2f}",
            f"Funding paid:           -${accounting.funding_paid:,.2f}",
            f"Account equity:          ${accounting.account_equity:,.2f}",
            f"Unrealized PnL:        {accounting.unrealized_pnl:+,.2f}",
            f"Final equity:            ${accounting.final_equity:,.2f}",
            f"Reconciliation residual: {accounting.residual:+.10f}",
            "",
            "PERFORMANCE",
            f"Net PnL:               {basic.net_pnl:+,.2f}",
            f"Return:                {basic.return_pct:+.4f}%",
            f"Realized trade events:  {basic.trade_count}",
            f"Win rate:               {basic.win_rate:.2f}%",
            "",
            "RISK",
            f"Max drawdown:           ${risk.max_drawdown:,.2f} ({risk.max_drawdown_pct:.2%})",
            f"Drawdown duration:      {risk.max_drawdown_duration_bars} bars",
            f"Annualized volatility:  {risk.annualized_volatility:.4f}",
            f"Sharpe / Sortino:       {_format_ratio(risk.sharpe_ratio)} / {_format_ratio(risk.sortino_ratio)}",
            f"CAGR / Calmar:          {risk.cagr:.4%} / {_format_ratio(risk.calmar_ratio)}",
        ]
    )


def _format_ratio(value: float | None) -> str:
    """
    [PURPOSE]: Format defined and undefined risk-adjusted ratios consistently for CLI output.
    [DEPENDENCIES]: Called by format_evaluation.
    [ARGS]: value — Ratio or None when mathematically undefined.
    [RETURNS]: Fixed-precision number or N/A.
    [SIDE EFFECTS]: None.
    """
    return "N/A" if value is None else f"{value:.4f}"


def main(argv: Sequence[str] | None = None) -> int:
    """
    [PURPOSE]: Execute the strict backtest CLI and print its complete evaluation.
    [DEPENDENCIES]: parse_args, run_strict_backtest, format_evaluation.
    [ARGS]: argv — Optional test argument sequence.
    [RETURNS]: Process status code zero after a successful run.
    [SIDE EFFECTS]: Reads dataset YAML and market-data storage; writes the report to stdout.
    """
    args = parse_args(argv)
    evaluation = run_strict_backtest(
        dataset_definition=args.dataset_definition,
        fast_period=args.fast_period,
        slow_period=args.slow_period,
        risk_free_rate=args.risk_free_rate,
    )
    print(format_evaluation(evaluation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
