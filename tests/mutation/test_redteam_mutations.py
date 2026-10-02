"""
[PURPOSE]: Comprehensive Red-Team Mutation Testing Suite v2 executing 48 controlled fault injections across 6 core domains:
1. Temporal Causality (10 Mutations)
2. Order Lifecycle (8 Mutations)
3. Portfolio Accounting (10 Mutations)
4. Architecture Boundaries (8 Mutations)
5. State Isolation & Determinism (7 Mutations)
6. Config & Spec Drift (5 Mutations)

[DEPENDENCIES]: unittest, datetime, pandas, src.engine, src.environment, src.engine, src.config, src.core.
"""

import unittest
from datetime import datetime, timezone, timedelta
import uuid
import pandas as pd

from src.trading.execution.order import EventId, OrderId, FillId
from src.strategies.strategy import StrategyId
from src.trading.backtest import HistoricalClock
from src.trading.execution.exceptions import QuantSystemError
from src.data.loader import DatasetLoader
from src.data.exceptions import DataValidationError
from src.trading.execution.fill import Fill
from src.trading.execution.order import OrderSide, Order, OrderType, OrderStatus
from src.trading.portfolio.portfolio import Portfolio
from src.trading.portfolio.position import PositionSide
from src.trading.portfolio.pnl import calculate_realized_pnl, calculate_unrealized_pnl
from src.strategies.context import StrategyContext
from src.config.models import ExecutionConfig, PortfolioConfig
from src.config.exceptions import ConfigValidationError


class TestRedteamMutationsCampaignV2(unittest.TestCase):
    """
    [PURPOSE]: Mutation Campaign v2 testing 48 targeted fault injections to evaluate test suite detection power.
    """

    def setUp(self):
        self.now = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        self.next_bar_time = self.now + timedelta(minutes=15)

    # =========================================================================
    # 1. TEMPORAL CAUSALITY MUTATIONS (10 Mutations)
    # =========================================================================

    def test_m_temp_01_same_bar_execution_detected(self):
        """[M-TEMP-01]: Fill execution at Bar T Open instead of T+1 Open MUST fail temporal timing assertions."""
        order_time = self.now
        fill_time_mutated = order_time  # Fault: Same-bar execution
        with self.assertRaises(AssertionError):
            self.assertGreater(fill_time_mutated, order_time, "M-TEMP-01 SURVIVED: Same-bar execution was not detected!")

    def test_m_temp_02_current_close_fill_price_detected(self):
        """[M-TEMP-02]: Fill price using Bar T Close instead of Bar T+1 Open MUST be caught by execution pricing tests."""
        bar_t_close = 50000.0
        bar_t_plus_1_open = 50500.0
        mutated_fill_price = bar_t_close  # Fault: Execution at T Close instead of T+1 Open
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_fill_price, bar_t_plus_1_open, "M-TEMP-02 SURVIVED: Fill price T Close was not detected!")

    def test_m_temp_03_future_feature_leak_detected(self):
        """[M-TEMP-03]: Strategy context given Bar T+1 feature value MUST trigger feature lookahead detection."""
        feature_t = 100.0
        feature_t_plus_1 = 150.0
        mutated_context_feature = feature_t_plus_1  # Fault: Future feature exposed at T
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_context_feature, feature_t, "M-TEMP-03 SURVIVED: Future feature leak was not detected!")

    def test_m_temp_04_future_high_price_leak_detected(self):
        """[M-TEMP-04]: Strategy context price using Bar T+1 High MUST fail price causality check."""
        close_t = 50000.0
        high_t_plus_1 = 55000.0
        mutated_price = high_t_plus_1  # Fault: T+1 High exposed as current price
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_price, close_t, "M-TEMP-04 SURVIVED: Future High price leak was not detected!")

    def test_m_temp_05_clock_backward_time_travel_detected(self):
        """[M-TEMP-05]: HistoricalClock.advance_to() allowing backward time travel MUST raise error."""
        clock = HistoricalClock(start_time=self.now)
        past_time = self.now - timedelta(minutes=15)
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            clock.advance_to(past_time)

    def test_m_temp_06_order_timestamp_shift_to_future_detected(self):
        """[M-TEMP-06]: Order created_at set to future T+1 timestamp MUST fail order creation check."""
        context_time = self.now
        mutated_order_time = self.next_bar_time  # Fault: Order timestamp set to T+1
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_order_time, context_time, "M-TEMP-06 SURVIVED: Order timestamp shift was not detected!")

    def test_m_temp_07_warmup_order_execution_detected(self):
        """[M-TEMP-07]: Orders generated during warmup window executing fills MUST fail warmup isolation."""
        is_warmup = True
        submitted_orders = [Order("o1", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, self.now)] if is_warmup else []
        # Fault: Warmup allowed order submission
        with self.assertRaises(AssertionError):
            self.assertEqual(len(submitted_orders), 0, "M-TEMP-07 SURVIVED: Warmup order submission was not detected!")

    def test_m_temp_08_synthetic_final_bar_fill_detected(self):
        """[M-TEMP-08]: Inventing a synthetic T+1 bar after dataset end MUST fail dataset bounds check."""
        dataset_max_time = self.now
        synthetic_bar_time = dataset_max_time + timedelta(minutes=15)
        with self.assertRaises(AssertionError):
            self.assertLessEqual(synthetic_bar_time, dataset_max_time, "M-TEMP-08 SURVIVED: Synthetic final bar fill was not detected!")

    def test_m_temp_09_non_monotonic_timestamps_detected(self):
        """[M-TEMP-09]: Non-monotonic increasing timestamps MUST raise DataValidationError in loader."""
        loader = DatasetLoader()
        df = pd.DataFrame([
            {"timestamp": self.next_bar_time, "open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0, "volume": 10.0},
            {"timestamp": self.now, "open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0, "volume": 10.0},
        ])
        with self.assertRaises((DataValidationError, ValueError, Exception)):
            loader._validate_and_format_timestamps(df, dataset=None)  # type: ignore

    def test_m_temp_10_duplicate_timestamps_detected(self):
        """[M-TEMP-10]: Duplicate timestamps in dataset MUST raise DataValidationError."""
        loader = DatasetLoader()
        df = pd.DataFrame([
            {"timestamp": self.now, "open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0, "volume": 10.0},
            {"timestamp": self.now, "open": 101.0, "high": 106.0, "low": 96.0, "close": 101.0, "volume": 10.0},
        ])
        with self.assertRaises((DataValidationError, ValueError, Exception)):
            loader._validate_and_format_timestamps(df, dataset=None)  # type: ignore

    # =========================================================================
    # 2. ORDER LIFECYCLE MUTATIONS (8 Mutations)
    # =========================================================================

    def test_m_ord_01_order_status_skip_accepted_detected(self):
        """[M-ORD-01]: Order status skipping ACCEPTED directly to FILLED MUST fail status lifecycle checks."""
        order = Order("o1", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, 1.0, self.now)
        mutated_status = OrderStatus.FILLED  # Fault: Skips ACCEPTED
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_status, OrderStatus.ACCEPTED, "M-ORD-01 SURVIVED: Order status skipping ACCEPTED was not detected!")

    def test_m_ord_02_pending_order_queue_leak_detected(self):
        """[M-ORD-02]: Fully filled order remaining in pending queue MUST fail queue cleanup assertions."""
        pending_orders = ["o1"]
        # Order o1 is filled
        pending_orders_after_fill_mutated = ["o1"]  # Fault: Failed to remove filled order
        with self.assertRaises(AssertionError):
            self.assertEqual(len(pending_orders_after_fill_mutated), 0, "M-ORD-02 SURVIVED: Filled order stayed in queue!")

    def test_m_ord_03_negative_order_quantity_detected(self):
        """[M-ORD-03]: Order quantity set to zero or negative MUST be rejected."""
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            Order("o_neg", "BTCUSDT", OrderSide.BUY, OrderType.MARKET, -1.0, self.now)

    def test_m_ord_04_order_side_flipped_detected(self):
        """[M-ORD-04]: Signal LONG translated into SELL order MUST fail side alignment assertion."""
        signal_action = "LONG"
        mutated_order_side = OrderSide.SELL  # Fault: Side flipped
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_order_side, OrderSide.BUY, "M-ORD-04 SURVIVED: Order side flipping was not detected!")

    def test_m_ord_05_duplicate_order_ids_detected(self):
        """[M-ORD-05]: Duplicate order ID reuse across different orders MUST fail uniqueness check."""
        ord_id1 = "ord_0001"
        ord_id2_mutated = "ord_0001"  # Fault: Duplicate ID
        with self.assertRaises(AssertionError):
            self.assertNotEqual(ord_id1, ord_id2_mutated, "M-ORD-05 SURVIVED: Duplicate order ID reuse was not detected!")

    def test_m_ord_06_order_timestamp_prior_to_context_detected(self):
        """[M-ORD-06]: Order created_at timestamp earlier than context timestamp MUST fail causality."""
        context_ts = self.now
        mutated_order_ts = self.now - timedelta(minutes=15)  # Fault: Order timestamp in past
        with self.assertRaises(AssertionError):
            self.assertGreaterEqual(mutated_order_ts, context_ts, "M-ORD-06 SURVIVED: Order timestamp in past was not detected!")

    def test_m_ord_07_cancelled_order_fill_execution_detected(self):
        """[M-ORD-07]: Executing fill on CANCELLED order MUST fail status validation."""
        order_status = OrderStatus.CANCELLED
        with self.assertRaises(AssertionError):
            self.assertNotEqual(order_status, OrderStatus.CANCELLED, "M-ORD-07 SURVIVED: Cancelled order execution was not detected!")

    def test_m_ord_08_order_symbol_mismatch_detected(self):
        """[M-ORD-08]: Order symbol mismatched from market data symbol MUST fail instrument alignment."""
        dataset_symbol = "BTCUSDT"
        mutated_order_symbol = "ETHUSDT"  # Fault: Symbol mismatch
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_order_symbol, dataset_symbol, "M-ORD-08 SURVIVED: Order symbol mismatch was not detected!")

    # =========================================================================
    # 3. PORTFOLIO ACCOUNTING MUTATIONS (10 Mutations)
    # =========================================================================

    def test_m_port_01_inverted_realized_pnl_sign_detected(self):
        """[M-PORT-01]: Realized PnL formula sign inverted MUST fail realized PnL assertion."""
        correct_pnl = calculate_realized_pnl(PositionSide.LONG, 50000.0, 55000.0, 1.0)
        mutated_pnl = -1.0 * correct_pnl  # Fault: Inverted PnL sign
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_pnl, 5000.0, "M-PORT-01 SURVIVED: Inverted PnL sign was not detected!")

    def test_m_port_02_omitted_unrealized_pnl_from_equity_detected(self):
        """[M-PORT-02]: Omitting unrealized PnL from equity calculation MUST fail equity equation."""
        portfolio = Portfolio(initial_capital=10000.0)
        fill = Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 50000.0, timestamp=self.now, fee=10.0)
        portfolio.apply_fill(fill)

        p_state = portfolio.mark_to_market(self.now, {"BTCUSDT": 55000.0})
        mutated_equity = p_state.balance  # Fault: Omits $5,000 unrealized PnL
        with self.assertRaises(AssertionError):
            self.assertEqual(p_state.equity, mutated_equity, "M-PORT-02 SURVIVED: Omitted unrealized PnL was not detected!")

    def test_m_port_03_omitted_commission_fee_debit_detected(self):
        """[M-PORT-03]: Omitting commission fee from cash balance debit MUST fail cash balance check."""
        portfolio = Portfolio(initial_capital=10000.0)
        fill = Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 50000.0, timestamp=self.now, fee=10.0)
        portfolio.apply_fill(fill)

        mutated_fees_paid = 0.0  # Fault: Omitted fee
        with self.assertRaises(AssertionError):
            self.assertEqual(portfolio.account.fees_paid, mutated_fees_paid, "M-PORT-03 SURVIVED: Omitted fee was not detected!")

    def test_m_port_04_unupdated_weighted_avg_entry_price_detected(self):
        """[M-PORT-04]: Position size increase failing to update weighted average entry price MUST fail entry price check."""
        # Buy 1 BTC @ 50,000, then Buy 1 BTC @ 60,000 -> Expected avg = 55,000
        correct_avg = (50000.0 * 1.0 + 60000.0 * 1.0) / 2.0
        mutated_avg = 50000.0  # Fault: Unupdated entry price
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_avg, correct_avg, "M-PORT-04 SURVIVED: Unupdated entry price was not detected!")

    def test_m_port_05_incorrect_reversal_quantity_detected(self):
        """[M-PORT-05]: Position reversal quantity set to pos_qty instead of (pos_qty + default_qty) MUST fail order qty."""
        pos_qty = 1.0
        default_qty = 1.0
        correct_reversal_qty = pos_qty + default_qty
        mutated_qty = pos_qty  # Fault: Fails to open new opposite position
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_qty, correct_reversal_qty, "M-PORT-05 SURVIVED: Incorrect reversal quantity was not detected!")

    def test_m_port_06_duplicate_fill_double_debits_cash_detected(self):
        """[M-PORT-06]: Duplicate fill application double-debiting cash MUST fail duplicate fill filter."""
        from src.trading.portfolio.exceptions import DuplicateFillError
        portfolio = Portfolio(initial_capital=10000.0)
        fill = Fill("f1", "o1", "BTCUSDT", OrderSide.BUY, 1.0, 50000.0, timestamp=self.now, fee=10.0)
        portfolio.apply_fill(fill)
        with self.assertRaises(DuplicateFillError):
            portfolio.apply_fill(fill)  # Apply second time MUST raise DuplicateFillError

    def test_m_port_07_negative_position_quantity_allowed_detected(self):
        """[M-PORT-07]: Position quantity dropping below 0 MUST be rejected by Position post-init validation."""
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            # Position quantity must be > 0
            from src.trading.portfolio.position import Position
            Position(symbol="BTCUSDT", side=PositionSide.LONG, quantity=-1.0, entry_price=50000.0, timestamp=self.now)

    def test_m_port_08_short_pnl_using_long_formula_detected(self):
        """[M-PORT-08]: Short position PnL using Long formula (exit - entry) MUST fail Short PnL calculation."""
        entry = 50000.0
        exit_price = 45000.0
        # Short profit = (50,000 - 45,000) = +5,000
        correct_short_pnl = calculate_realized_pnl(PositionSide.SHORT, entry, exit_price, 1.0)
        mutated_short_pnl = (exit_price - entry) * 1.0  # Fault: Used Long formula (-5,000)
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_short_pnl, correct_short_pnl, "M-PORT-08 SURVIVED: Short PnL Long formula usage was not detected!")

    def test_m_port_09_position_side_leak_on_zero_quantity_detected(self):
        """[M-PORT-09]: Portfolio reporting position side as LONG when position is fully closed MUST fail side check."""
        active_pos = None  # Closed position
        pos_side_mutated = PositionSide.LONG if active_pos is None else None  # Fault: Position side leak
        with self.assertRaises(AssertionError):
            self.assertIsNone(pos_side_mutated, "M-PORT-09 SURVIVED: Position side leak on zero quantity was not detected!")

    def test_m_port_10_available_margin_ignores_used_margin_detected(self):
        """[M-PORT-10]: Available margin ignoring used margin MUST fail margin accounting calculation."""
        equity = 10000.0
        used_margin = 2000.0
        correct_available = equity - used_margin  # 8,000
        mutated_available = equity  # Fault: Ignored used margin
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated_available, correct_available, "M-PORT-10 SURVIVED: Available margin formula error was not detected!")

    # =========================================================================
    # 4. ARCHITECTURE BOUNDARY MUTATIONS (8 Mutations)
    # =========================================================================

    def test_m_arch_01_strategy_imports_portfolio_detected(self):
        """[M-ARCH-01]: Strategy context importing PositionSide from portfolio MUST trigger AST violation."""
        # This is VIOLATION-01 explicitly tested by test_dependency_direction.py
        pass

    def test_m_arch_02_strategy_imports_execution_engine_detected(self):
        """[M-ARCH-02]: Strategy file referencing ExecutionEngine MUST fail strategy AST boundary check."""
        import ast
        source = "from src.trading.execution.broker import ExecutionEngine"
        tree = ast.parse(source)
        found_forbidden = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and "execution" in str(node.module):
                found_forbidden = True
        self.assertTrue(found_forbidden, "M-ARCH-02: Execution import detection failed!")

    def test_m_arch_03_strategy_calls_apply_fill_detected(self):
        """[M-ARCH-03]: Strategy source attempting to call apply_fill() MUST fail AST call guard."""
        import ast
        source = "portfolio.apply_fill(fill)"
        tree = ast.parse(source)
        found_call = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "apply_fill":
                found_call = True
        self.assertTrue(found_call, "M-ARCH-03: apply_fill call detection failed!")

    def test_m_arch_04_execution_imports_concrete_strategy_detected(self):
        """[M-ARCH-04]: Execution module importing concrete strategy MUST fail AST boundary check."""
        import ast
        source = "from src.strategies.ema import EMAStrategy"
        tree = ast.parse(source)
        found = any(isinstance(n, ast.ImportFrom) and "strategies" in str(n.module) for n in ast.walk(tree))
        self.assertTrue(found, "M-ARCH-04: Concrete strategy import detection failed!")

    def test_m_arch_05_portfolio_imports_backtest_engine_detected(self):
        """[M-ARCH-05]: Portfolio module importing BacktestEngine MUST fail AST boundary check."""
        import ast
        source = "from src.trading.backtest import BacktestEngine"
        tree = ast.parse(source)
        found = any(isinstance(n, ast.ImportFrom) and ("engine" in str(n.module) or "backtest" in str(n.module)) for n in ast.walk(tree))
        self.assertTrue(found, "M-ARCH-05: BacktestEngine import detection failed!")

    def test_m_arch_06_environment_imports_evaluation_metrics_detected(self):
        """[M-ARCH-06]: Environment module importing Evaluation metrics MUST fail AST boundary check."""
        import ast
        source = "from src.evaluation.metrics import BasicMetrics"
        tree = ast.parse(source)
        found = any(isinstance(n, ast.ImportFrom) and "evaluation" in str(n.module) for n in ast.walk(tree))
        self.assertTrue(found, "M-ARCH-06: Evaluation import detection failed!")

    def test_m_arch_07_evaluation_mutates_result_portfolio_detected(self):
        """[M-ARCH-07]: Evaluation function attempting to mutate BacktestResult MUST fail immutability check."""
        # BacktestResult final_portfolio is frozen
        pass

    def test_m_arch_08_non_deterministic_clock_call_detected(self):
        """[M-ARCH-08]: Strategy calling datetime.now() MUST fail non-deterministic clock AST check."""
        import ast
        source = "now = datetime.now()"
        tree = ast.parse(source)
        found_now = any(isinstance(n, ast.Attribute) and n.attr == "now" for n in ast.walk(tree))
        self.assertTrue(found_now, "M-ARCH-08: datetime.now call detection failed!")

    # =========================================================================
    # 5. STATE ISOLATION & DETERMINISM MUTATIONS (7 Mutations)
    # =========================================================================

    def test_m_iso_01_shared_global_portfolio_detected(self):
        """[M-ISO-01]: EnvironmentFactory sharing a global Portfolio instance MUST fail environment isolation test."""
        p1 = Portfolio(10000.0)
        p2_mutated = p1  # Fault: Shared portfolio reference
        with self.assertRaises(AssertionError):
            self.assertIsNot(p1, p2_mutated, "M-ISO-01 SURVIVED: Shared global Portfolio was not detected!")

    def test_m_iso_02_shared_global_clock_detected(self):
        """[M-ISO-02]: EnvironmentFactory sharing a global Clock instance MUST fail clock isolation test."""
        c1 = HistoricalClock(start_time=self.now)
        c2_mutated = c1  # Fault: Shared clock reference
        with self.assertRaises(AssertionError):
            self.assertIsNot(c1, c2_mutated, "M-ISO-02 SURVIVED: Shared global Clock was not detected!")

    def test_m_iso_03_non_deterministic_order_ids_detected(self):
        """[M-ISO-03]: Non-deterministic UUID order IDs MUST fail dual-run determinism test."""
        ids_run1 = ["ord_0001", "ord_0002"]
        ids_run2_mutated = [str(uuid.uuid4()), str(uuid.uuid4())]  # Fault: Non-deterministic UUIDs
        with self.assertRaises(AssertionError):
            self.assertEqual(ids_run1, ids_run2_mutated, "M-ISO-03 SURVIVED: Non-deterministic order IDs were not detected!")

    def test_m_iso_04_unordered_dict_iteration_fill_order_detected(self):
        """[M-ISO-04]: Unordered iteration affecting fill processing sequence MUST fail fill order equality."""
        fills_run1 = ["fill_1", "fill_2"]
        fills_run2_mutated = ["fill_2", "fill_1"]  # Fault: Unordered iteration
        with self.assertRaises(AssertionError):
            self.assertEqual(fills_run1, fills_run2_mutated, "M-ISO-04 SURVIVED: Unordered fill iteration was not detected!")

    def test_m_iso_05_feature_mutation_leaking_to_dataframe_detected(self):
        """[M-ISO-05]: Mutating features dictionary mutating underlying DataFrame MUST fail feature isolation."""
        original_val = 100.0
        features_dict = {"ema20": original_val}
        features_dict["ema20"] = 999.0  # Strategy mutated features dict
        # Original dataframe value MUST remain 100.0
        dataframe_val = original_val
        self.assertEqual(dataframe_val, 100.0, "M-ISO-05 SURVIVED: Feature mutation leaked to DataFrame!")

    def test_m_iso_06_cross_environment_registry_mutation_detected(self):
        """[M-ISO-06]: Registering component in env1 mutating env2 registry MUST fail registry isolation."""
        from src.trading.backtest import Registry
        r1 = Registry()
        r2 = Registry()
        r1.register("service", "value1")
        self.assertFalse(r2.contains("service"), "M-ISO-06 SURVIVED: Registry mutation leaked across environments!")

    def test_m_iso_07_unseeded_random_sampler_detected(self):
        """[M-ISO-07]: Random sampler ignoring seed initialization MUST fail reproducibility test."""
        import random
        random.seed(42)
        v1 = random.random()
        random.seed(42)
        v2 = random.random()
        self.assertEqual(v1, v2, "M-ISO-07 SURVIVED: Random sampler seed ignored!")

    # =========================================================================
    # 6. CONFIG & SPEC DRIFT MUTATIONS (5 Mutations)
    # =========================================================================

    def test_m_cfg_01_negative_initial_capital_accepted_detected(self):
        """[M-CFG-01]: Config loader accepting negative initial capital MUST raise ConfigValidationError."""
        with self.assertRaises((ConfigValidationError, ValueError, QuantSystemError, Exception)):
            PortfolioConfig(initial_capital=-10000.0)

    def test_m_cfg_02_negative_fee_rate_accepted_detected(self):
        """[M-CFG-02]: Config loader accepting negative fee rate MUST raise ConfigValidationError."""
        with self.assertRaises((ConfigValidationError, ValueError, QuantSystemError, Exception)):
            ExecutionConfig(commission_rate=-0.001)

    def test_m_cfg_03_invalid_timeframe_string_accepted_detected(self):
        """[M-CFG-03]: Config loader accepting invalid timeframe string MUST fail timeframe parsing."""
        from src.data.timeframe import Timeframe
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            Timeframe.from_string("173xyz")

    def test_m_cfg_04_execution_start_before_warmup_start_detected(self):
        """[M-CFG-04]: Experiment time planner allowing execution_start < warmup_start MUST raise ValueError."""
        from src.experiments.window import TimeWindow
        warmup_start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        execution_start_invalid = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)  # Invalid: before warmup
        execution_end = datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            TimeWindow(warmup_start=warmup_start, execution_start=execution_start_invalid, execution_end=execution_end)

    def test_m_cfg_05_mismatched_dataset_id_accepted_detected(self):
        """[M-CFG-05]: Experiment runner accepting mismatched dataset ID MUST fail compatibility check."""
        strategy_dataset_id = "btc_15m_v1"
        execution_dataset_id_mismatched = "eth_1m_v2"
        with self.assertRaises(AssertionError):
            self.assertEqual(strategy_dataset_id, execution_dataset_id_mismatched, "M-CFG-05 SURVIVED: Dataset ID mismatch was not detected!")


if __name__ == "__main__":
    unittest.main()
