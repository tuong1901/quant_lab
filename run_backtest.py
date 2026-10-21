"""Strict YAML-configured production backtest runner."""

from dataclasses import dataclass
import argparse
import logging
from pathlib import Path

import pandas as pd

from src.config.runner import BacktestRunnerConfig, load_backtest_runner_config
from src.data.dataset import Dataset
from src.data.loader import DatasetLoader
from src.evaluation import AccountingReconciliation, BasicMetrics, EquityRiskMetrics, calculate_accounting_reconciliation, calculate_basic_metrics, calculate_equity_risk_metrics
from src.features.indicators import calculate_causal_atr
from src.strategies.ema import EMAStrategy
from src.trading.backtest import BacktestEngine, BacktestResult, ExecutionContext, HistoricalClock
from src.trading.execution import ExecutionEngine, FixedSlippageModel, PercentageFeeModel
from src.trading.portfolio import Portfolio
from src.trading.portfolio.exceptions import PortfolioException

logger = logging.getLogger(__name__)


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
        """
        [PURPOSE]: Capture accounting and progress when portfolio processing fails.
        [DEPENDENCIES]: Portfolio and BacktestEngine partial state.
        [ARGS]: portfolio, engine — runtime state; cause — original exception.
        [RETURNS]: None.
        [SIDE EFFECTS]: Initializes exception and logs failure context.
        """
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
        logger.debug("Captured portfolio failure balance=%s orders=%s fills=%s cause=%s",
                     self.balance, self.order_count, self.fill_count, cause)


def add_ema_features(frame: pd.DataFrame, fast_period: int, slow_period: int, atr_period: int = 14) -> pd.DataFrame:
    """
    [PURPOSE]: Add EMA columns required by the reference strategy.
    [DEPENDENCIES]: Called by run_strict_backtest.
    [ARGS]: frame — OHLCV frame; fast_period, slow_period — EMA periods; atr_period — ATR period.
    [RETURNS]: Copied frame with EMA columns.
    [SIDE EFFECTS]: Logs feature settings; raises ValueError for invalid periods.
    """
    logger.info("Building features rows=%s ema_fast=%s ema_slow=%s atr_period=%s",
                len(frame), fast_period, slow_period, atr_period)
    if fast_period <= 0 or slow_period <= 0 or fast_period >= slow_period:
        raise ValueError("EMA periods must be positive and fast_period must be smaller than slow_period.")
    if isinstance(atr_period, bool) or not isinstance(atr_period, int) or atr_period <= 0:
        raise ValueError("atr_period must be a positive integer.")
    featured = frame.copy()
    featured[f"ema{fast_period}"] = featured["close"].ewm(span=fast_period, adjust=False).mean()
    featured[f"ema{slow_period}"] = featured["close"].ewm(span=slow_period, adjust=False).mean()
    featured["atr"] = calculate_causal_atr(featured, period=atr_period)
    logger.debug("Features ready columns=%s", list(featured.columns))
    return featured


def run_strict_backtest(config: BacktestRunnerConfig) -> StrictBacktestEvaluation:
    """
    [PURPOSE]: Run Dataset YAML through strict loading, EMA strategy, backtest, and evaluation.
    [DEPENDENCIES]: DatasetLoader, EMAStrategy, BacktestEngine, evaluation API.
    [ARGS]: config — Typed settings loaded from config/backtest.yaml.
    [RETURNS]: Complete strict evaluation.
    [SIDE EFFECTS]: Reads Dataset YAML and market storage; logs settings, completion and failures.
    """
    logger.info("Starting strict backtest settings=%s", config)
    try:
        evaluation = _run_strict_backtest(config)
    except Exception:
        logger.exception("Strict backtest failed dataset_definition=%s", config.dataset_definition)
        raise
    logger.info("Backtest completed bars=%s orders=%s fills=%s final_equity=%s residual=%s",
                evaluation.result.bars_processed, len(evaluation.result.orders),
                len(evaluation.result.fills), evaluation.accounting.final_equity,
                evaluation.accounting.residual)
    return evaluation


def _run_strict_backtest(config: BacktestRunnerConfig) -> StrictBacktestEvaluation:
    """
    [PURPOSE]: Assemble and execute the configured dataset-to-evaluation pipeline.
    [DEPENDENCIES]: DatasetLoader, feature builder, trading engine and evaluation.
    [ARGS]: config — validated runtime settings.
    [RETURNS]: Completed evaluation.
    [SIDE EFFECTS]: Reads dataset files, mutates runtime state, logs setup; propagates errors.
    """
    logger.info("Loading dataset descriptor=%s", config.dataset_definition)
    dataset = Dataset.from_yaml(config.dataset_definition)
    data = DatasetLoader().load(dataset)
    frame = data.df.iloc[:config.bar_limit].copy() if config.bar_limit else data.df
    if frame.empty:
        raise ValueError("Selected backtest data is empty.")
    first_timestamp = frame["timestamp"].iloc[0] if "timestamp" in frame else frame.index[0]
    last_timestamp = frame["timestamp"].iloc[-1] if "timestamp" in frame else frame.index[-1]
    logger.info("Dataset ready identity=%s symbol=%s timeframe=%s loaded_rows=%s selected_rows=%s range=%s..%s",
                dataset.identity, dataset.market.symbol, dataset.timeframe, len(data.df), len(frame),
                first_timestamp, last_timestamp)
    clock = HistoricalClock(first_timestamp)
    context = ExecutionContext(
        clock=clock,
        run=f"strict:{dataset.identity}",
        dataset_id=dataset.identity,
        execution_id="strict_ohlc",
    )
    portfolio = Portfolio(initial_capital=config.initial_capital, leverage=config.leverage)
    execution = ExecutionEngine(
        slippage_model=FixedSlippageModel(config.slippage_bps),
        fee_model=PercentageFeeModel(config.maker_fee_bps, config.taker_fee_bps),
    )
    logger.info("Runtime ready clock=%s capital=%s leverage=%s slippage_bps=%s maker_bps=%s taker_bps=%s",
                clock.now(), config.initial_capital, config.leverage, config.slippage_bps,
                config.maker_fee_bps, config.taker_fee_bps)
    engine = BacktestEngine(
        strategy=EMAStrategy(config.fast_period, config.slow_period),
        portfolio=portfolio,
        broker=execution,
        clock=clock,
        context=context,
        symbol=dataset.market.symbol,
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
        result = engine.run(add_ema_features(frame, config.fast_period, config.slow_period, config.atr_period))
    except PortfolioException as error:
        raise AccountDepletedError(portfolio, engine, error) from error
    logger.debug("Evaluating result risk_free_rate=%s", config.risk_free_rate)
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
    [SIDE EFFECTS]: Emits a DEBUG trace.
    """
    logger.debug("Formatting evaluation bars=%s", evaluation.result.bars_processed)
    basic, risk, accounting = evaluation.basic, evaluation.risk, evaluation.accounting
    ratio = lambda value: "N/A" if value is None else f"{value:.4f}"
    return "\n".join(["STRICT BACKTEST EVALUATION", "=" * 72, f"Bars processed:         {evaluation.result.bars_processed}", f"Signals / orders / fills:{len(evaluation.result.signals)} / {len(evaluation.result.orders)} / {len(evaluation.result.fills)}", "", "ACCOUNTING RECONCILIATION", f"Initial capital:         ${accounting.initial_capital:,.2f}", f"Realized PnL:          {accounting.realized_pnl:+,.2f}", f"Fees paid:              -${accounting.total_fees:,.2f}", f"Funding paid:           -${accounting.funding_paid:,.2f}", f"Account equity:          ${accounting.account_equity:,.2f}", f"Unrealized PnL:        {accounting.unrealized_pnl:+,.2f}", f"Final equity:            ${accounting.final_equity:,.2f}", f"Reconciliation residual: {accounting.residual:+.10f}", "", "PERFORMANCE", f"Net PnL:               {basic.net_pnl:+,.2f}", f"Return:                {basic.return_pct:+.4f}%", f"Realized trade events:  {basic.trade_count}", f"Win rate:               {basic.win_rate:.2f}%", "", "RISK", f"Max drawdown:           ${risk.max_drawdown:,.2f} ({risk.max_drawdown_pct:.2%})", f"Drawdown duration:      {risk.max_drawdown_duration_bars} bars", f"Annualized volatility:  {risk.annualized_volatility:.4f}", f"Sharpe / Sortino:       {ratio(risk.sharpe_ratio)} / {ratio(risk.sortino_ratio)}", f"CAGR / Calmar:          {risk.cagr:.4%} / {ratio(risk.calmar_ratio)}"])


def configure_logging(level: str = "INFO", log_path: str = "logs/backtest.log") -> None:
    """
    [PURPOSE]: Configure CLI console and append-only file diagnostics.
    [DEPENDENCIES]: Called only by main; Python logging.
    [ARGS]: level — INFO or DEBUG; log_path — output path.
    [RETURNS]: None.
    [SIDE EFFECTS]: Creates log directory/file, replaces root handlers; may raise OSError.
    """
    destination = Path(log_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(destination, mode="a", encoding="utf-8")],
        force=True,
    )
    logger.info("Logging initialized level=%s file=%s", level, destination.resolve())


def main(argv: list[str] | None = None) -> int:
    """
    [PURPOSE]: Execute the YAML-configured strict backtest.
    [DEPENDENCIES]: load_backtest_runner_config and run_strict_backtest.
    [ARGS]: argv — optional CLI arguments; defaults to process arguments.
    [RETURNS]: Zero on success, two on depletion, one on other runtime failure.
    [SIDE EFFECTS]: Initializes logs, reads YAML/data and writes report text to stdout.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-level", choices=("INFO", "DEBUG"), default="INFO")
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    logger.info("Starting YAML-configured runner")
    try:
        config = load_backtest_runner_config()
        print(format_evaluation(run_strict_backtest(config)))
        logger.info("Runner completed successfully")
        return 0
    except AccountDepletedError as error:
        logger.error("Account depleted: %s", error)
        print(_format_account_depleted_log(error))
        return 2
    except Exception:
        logger.exception("Runner failed")
        return 1


def _format_account_depleted_log(error: AccountDepletedError) -> str:
    """
    [PURPOSE]: Render a factual accounting explanation for an exhausted account.
    [DEPENDENCIES]: AccountDepletedError values captured from Portfolio.
    [ARGS]: error — Account depletion failure.
    [RETURNS]: Human-readable terminal log.
    [SIDE EFFECTS]: Emits a DEBUG trace.
    """
    logger.debug("Formatting depletion report balance=%s stop=%s", error.balance, error.stop_time)
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
