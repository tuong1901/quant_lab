"""Strict YAML-configured production backtest runner."""

from dataclasses import dataclass

import pandas as pd

from src.config.runner import BacktestRunnerConfig, load_backtest_runner_config
from src.data.dataset import Dataset
from src.data.loader import DatasetLoader
from src.evaluation import AccountingReconciliation, BasicMetrics, EquityRiskMetrics, calculate_accounting_reconciliation, calculate_basic_metrics, calculate_equity_risk_metrics
from src.features.indicators import calculate_causal_atr
from src.strategies.ema import EMAStrategy
from src.trading.backtest import BacktestEngine, BacktestResult
from src.trading.execution import ExecutionEngine, FixedSlippageModel, PercentageFeeModel
from src.trading.portfolio import Portfolio
from src.trading.portfolio.exceptions import PortfolioException


@dataclass(frozen=True)
class StrictBacktestEvaluation:
    """Complete read-only evaluation produced by one strict backtest."""
    result: BacktestResult
    basic: BasicMetrics
    risk: EquityRiskMetrics | None
    accounting: AccountingReconciliation


class AccountDepletedError(RuntimeError):
    """Raised with final accounting values when a backtest account cannot continue."""

    def __init__(self, portfolio: Portfolio, engine: BacktestEngine, cause: PortfolioException) -> None:
        self.balance = portfolio.account.balance
        self.realized_pnl = portfolio.account.realized_pnl
        self.fees_paid = portfolio.account.fees_paid
        self.funding_paid = portfolio.account.funding_paid
        self.start_time = engine.partial_start_timestamp
        self.stop_time = engine.partial_last_timestamp
        self.signal_count = len(engine.partial_signals)
        self.order_count = len(engine.partial_orders)
        self.fill_count = len(engine.partial_fills)
        self.last_order_time = engine.partial_orders[-1].created_at if engine.partial_orders else None
        self.last_fill_time = engine.partial_fills[-1].timestamp if engine.partial_fills else None
        super().__init__(str(cause))


def add_ema_features(frame: pd.DataFrame, fast_period: int, slow_period: int) -> pd.DataFrame:
    """
    [PURPOSE]: Add EMA columns required by the reference strategy.
    [DEPENDENCIES]: Called by run_strict_backtest.
    [ARGS]: frame — Canonical OHLCV frame; fast_period, slow_period — Positive EMA periods.
    [RETURNS]: Copied frame with EMA columns.
    [SIDE EFFECTS]: Raises ValueError for invalid periods.
    """
    if fast_period <= 0 or slow_period <= 0 or fast_period >= slow_period:
        raise ValueError("EMA periods must be positive and fast_period must be smaller than slow_period.")
    featured = frame.copy()
    featured[f"ema{fast_period}"] = featured["close"].ewm(span=fast_period, adjust=False).mean()
    featured[f"ema{slow_period}"] = featured["close"].ewm(span=slow_period, adjust=False).mean()
    featured["atr"] = calculate_causal_atr(featured)
    return featured


def run_strict_backtest(config: BacktestRunnerConfig) -> StrictBacktestEvaluation:
    """
    [PURPOSE]: Run Dataset YAML through strict loading, EMA strategy, backtest, and evaluation.
    [DEPENDENCIES]: DatasetLoader, EMAStrategy, BacktestEngine, evaluation API.
    [ARGS]: config — Typed settings loaded from config/backtest.yaml.
    [RETURNS]: Complete strict evaluation.
    [SIDE EFFECTS]: Reads Dataset YAML and market storage.
    """
    dataset = Dataset.from_yaml(config.dataset_definition)
    data = DatasetLoader().load(dataset)
    frame = data.df.iloc[:config.bar_limit].copy() if config.bar_limit else data.df
    portfolio = Portfolio(initial_capital=config.initial_capital, leverage=config.leverage)
    execution = ExecutionEngine(
        slippage_model=FixedSlippageModel(config.slippage_bps),
        fee_model=PercentageFeeModel(config.maker_fee_bps, config.taker_fee_bps),
    )
    engine = BacktestEngine(
        strategy=EMAStrategy(config.fast_period, config.slow_period),
        portfolio=portfolio,
        broker=execution,
        default_order_quantity=config.fixed_quantity,
        sizing_mode=config.sizing_mode,
        risk_per_trade_pct=config.risk_per_trade_pct,
        max_position_size=config.max_position_size,
        max_notional=config.max_notional,
        allow_short=config.allow_short,
        atr_multiplier=config.atr_multiplier,
        reward_to_risk=config.reward_to_risk,
    )
    try:
        result = engine.run(add_ema_features(frame, config.fast_period, config.slow_period))
    except PortfolioException as error:
        raise AccountDepletedError(portfolio, engine, error) from error
    basic = calculate_basic_metrics(result)
    return StrictBacktestEvaluation(
        result=result,
        basic=basic,
        risk=calculate_equity_risk_metrics(basic.equity_curve, dataset.timeframe, config.risk_free_rate),
        accounting=calculate_accounting_reconciliation(result),
    )


def format_evaluation(evaluation: StrictBacktestEvaluation) -> str:
    """
    [PURPOSE]: Render accounting, performance, and risk metrics for the terminal.
    [DEPENDENCIES]: StrictBacktestEvaluation.
    [ARGS]: evaluation — Completed strict result.
    [RETURNS]: Human-readable report.
    [SIDE EFFECTS]: None.
    """
    basic, risk, accounting = evaluation.basic, evaluation.risk, evaluation.accounting
    ratio = lambda value: "N/A" if value is None else f"{value:.4f}"
    return "\n".join(["STRICT BACKTEST EVALUATION", "=" * 72, f"Bars processed:         {evaluation.result.bars_processed}", f"Signals / orders / fills:{len(evaluation.result.signals)} / {len(evaluation.result.orders)} / {len(evaluation.result.fills)}", "", "ACCOUNTING RECONCILIATION", f"Initial capital:         ${accounting.initial_capital:,.2f}", f"Realized PnL:          {accounting.realized_pnl:+,.2f}", f"Fees paid:              -${accounting.total_fees:,.2f}", f"Funding paid:           -${accounting.funding_paid:,.2f}", f"Account equity:          ${accounting.account_equity:,.2f}", f"Unrealized PnL:        {accounting.unrealized_pnl:+,.2f}", f"Final equity:            ${accounting.final_equity:,.2f}", f"Reconciliation residual: {accounting.residual:+.10f}", "", "PERFORMANCE", f"Net PnL:               {basic.net_pnl:+,.2f}", f"Return:                {basic.return_pct:+.4f}%", f"Realized trade events:  {basic.trade_count}", f"Win rate:               {basic.win_rate:.2f}%", "", "RISK", f"Max drawdown:           ${risk.max_drawdown:,.2f} ({risk.max_drawdown_pct:.2%})", f"Drawdown duration:      {risk.max_drawdown_duration_bars} bars", f"Annualized volatility:  {risk.annualized_volatility:.4f}", f"Sharpe / Sortino:       {ratio(risk.sharpe_ratio)} / {ratio(risk.sortino_ratio)}", f"CAGR / Calmar:          {risk.cagr:.4%} / {ratio(risk.calmar_ratio)}"])


def main() -> int:
    """
    [PURPOSE]: Execute the YAML-configured strict backtest.
    [DEPENDENCIES]: load_backtest_runner_config and run_strict_backtest.
    [ARGS]: None.
    [RETURNS]: Zero after successful execution.
    [SIDE EFFECTS]: Reads YAML/data and writes report text to stdout.
    """
    try:
        config = load_backtest_runner_config()
        print(format_evaluation(run_strict_backtest(config)))
        return 0
    except AccountDepletedError as error:
        print(_format_account_depleted_log(error))
        return 2


def _format_account_depleted_log(error: AccountDepletedError) -> str:
    """
    [PURPOSE]: Render a factual accounting explanation for an exhausted account.
    [DEPENDENCIES]: AccountDepletedError values captured from Portfolio.
    [ARGS]: error — Account depletion failure.
    [RETURNS]: Human-readable terminal log.
    [SIDE EFFECTS]: None.
    """
    loss_text = "Realized trading losses contributed to depletion." if error.realized_pnl < 0 else "Execution costs and account cash flow caused the negative balance."
    return "\n".join([
        "ACCOUNT DEPLETED",
        "=" * 72,
        f"Run period: {error.start_time.isoformat() if error.start_time else 'N/A'} -> {error.stop_time.isoformat() if error.stop_time else 'N/A'}",
        f"Signals / orders / fills: {error.signal_count} / {error.order_count} / {error.fill_count}",
        f"Last order / fill: {error.last_order_time.isoformat() if error.last_order_time else 'N/A'} / {error.last_fill_time.isoformat() if error.last_fill_time else 'N/A'}",
        f"Reason: {loss_text}",
        f"Balance at stop:         ${error.balance:,.2f}",
        f"Realized PnL:           {error.realized_pnl:+,.2f}",
        f"Fees paid:              -${error.fees_paid:,.2f}",
        f"Funding paid:           -${error.funding_paid:,.2f}",
        f"Engine detail: {error}",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
