"""P0 accounting contracts for fills, positions, PnL, fees, MTM, and equity."""

from datetime import datetime, timedelta, timezone
import unittest

from src.trading.execution.fill import Fill
from src.trading.execution.order import OrderSide
from src.trading.portfolio.exceptions import DuplicateFillError
from src.trading.portfolio.pnl import calculate_realized_pnl, calculate_unrealized_pnl
from src.trading.portfolio.portfolio import Portfolio
from src.trading.portfolio.position import PositionSide


UTC = timezone.utc
START_TIME = datetime(2026, 10, 5, tzinfo=UTC)


def make_fill(
    fill_id: str,
    side: OrderSide,
    price: float,
    quantity: float = 1.0,
    fee: float = 0.0,
    symbol: str = "BTCUSDT",
    minute: int = 0,
) -> Fill:
    """
    [PURPOSE]: Build a deterministic valid fill for portfolio contract tests.
    [DEPENDENCIES]: Used only by this test module.
    [ARGS]: Fill identifiers, execution direction, economics, symbol, and timestamp offset.
    [RETURNS]: Immutable Fill ready for Portfolio.apply_fill.
    [SIDE EFFECTS]: None.
    """
    return Fill(
        fill_id=fill_id,
        order_id=f"order-{fill_id}",
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        fee=fee,
        timestamp=START_TIME + timedelta(minutes=minute),
    )


class TestPortfolioContracts(unittest.TestCase):
    """P0 portfolio invariants from Fill through Position, PnL, costs, and Equity."""

    def test_pnl_formula_long_and_short_profit_loss_and_flat(self):
        cases = [
            (PositionSide.LONG, 100.0, 120.0, 1.0, 20.0),
            (PositionSide.LONG, 100.0, 80.0, 1.0, -20.0),
            (PositionSide.LONG, 100.0, 100.0, 1.0, 0.0),
            (PositionSide.SHORT, 100.0, 80.0, 1.0, 20.0),
            (PositionSide.SHORT, 100.0, 120.0, 1.0, -20.0),
            (PositionSide.SHORT, 100.0, 100.0, 1.0, 0.0),
        ]
        for side, entry, exit_price, quantity, expected in cases:
            with self.subTest(side=side, exit_price=exit_price):
                self.assertEqual(calculate_realized_pnl(side, entry, exit_price, quantity), expected)
                self.assertEqual(calculate_unrealized_pnl(side, entry, exit_price, quantity), expected)

    def test_pf_001_and_002_open_long_and_short_do_not_realize_pnl(self):
        for side, expected_side in ((OrderSide.BUY, PositionSide.LONG), (OrderSide.SELL, PositionSide.SHORT)):
            with self.subTest(side=side):
                portfolio = Portfolio()
                state = portfolio.apply_fill(make_fill(f"open-{side.value}", side, 100.0))
                position = state.positions["BTCUSDT"]
                self.assertEqual(position.side, expected_side)
                self.assertEqual(position.quantity, 1.0)
                self.assertEqual(position.average_entry_price, 100.0)
                self.assertEqual(state.realized_pnl, 0.0)

    def test_pf_003_and_004_weighted_average_long_and_short_with_unequal_quantity(self):
        cases = [
            (OrderSide.BUY, 100.0, 130.0, PositionSide.LONG, 110.0),
            (OrderSide.SELL, 100.0, 70.0, PositionSide.SHORT, 90.0),
        ]
        for side, first_price, second_price, expected_side, expected_average in cases:
            with self.subTest(side=side):
                portfolio = Portfolio()
                portfolio.apply_fill(make_fill(f"first-{side.value}", side, first_price, quantity=2.0))
                state = portfolio.apply_fill(make_fill(f"second-{side.value}", side, second_price, quantity=1.0, minute=15))
                position = state.positions["BTCUSDT"]
                self.assertEqual(position.side, expected_side)
                self.assertEqual(position.quantity, 3.0)
                self.assertEqual(position.average_entry_price, expected_average)
                self.assertEqual(state.realized_pnl, 0.0)

    def test_pf_005_partial_close_long_realizes_only_closed_quantity(self):
        portfolio = Portfolio()
        portfolio.apply_fill(make_fill("long-open", OrderSide.BUY, 100.0, quantity=3.0))
        state = portfolio.apply_fill(make_fill("long-reduce", OrderSide.SELL, 120.0, minute=15))
        position = state.positions["BTCUSDT"]

        self.assertEqual(state.realized_pnl, 20.0)
        self.assertEqual(position.quantity, 2.0)
        self.assertEqual(position.average_entry_price, 100.0)

    def test_pf_006_partial_close_short_realizes_only_closed_quantity(self):
        portfolio = Portfolio()
        portfolio.apply_fill(make_fill("short-open", OrderSide.SELL, 100.0, quantity=3.0))
        state = portfolio.apply_fill(make_fill("short-reduce", OrderSide.BUY, 80.0, minute=15))
        position = state.positions["BTCUSDT"]

        self.assertEqual(state.realized_pnl, 20.0)
        self.assertEqual(position.quantity, 2.0)
        self.assertEqual(position.average_entry_price, 100.0)

    def test_pf_007_and_008_full_close_removes_position_for_long_and_short(self):
        cases = [(OrderSide.BUY, OrderSide.SELL, 20.0), (OrderSide.SELL, OrderSide.BUY, -20.0)]
        for open_side, close_side, expected_pnl in cases:
            with self.subTest(open_side=open_side):
                portfolio = Portfolio()
                portfolio.apply_fill(make_fill(f"open-{open_side.value}", open_side, 100.0))
                state = portfolio.apply_fill(make_fill(f"close-{open_side.value}", close_side, 120.0, minute=15))
                self.assertNotIn("BTCUSDT", state.positions)
                self.assertEqual(state.realized_pnl, expected_pnl)
                self.assertEqual(state.unrealized_pnl, 0.0)

    def test_pf_009_and_010_reversal_closes_old_position_then_opens_remainder(self):
        cases = [
            (OrderSide.BUY, OrderSide.SELL, 90.0, PositionSide.SHORT, -20.0),
            (OrderSide.SELL, OrderSide.BUY, 110.0, PositionSide.LONG, -20.0),
        ]
        for open_side, reversal_side, reversal_price, expected_side, expected_pnl in cases:
            with self.subTest(open_side=open_side):
                portfolio = Portfolio()
                portfolio.apply_fill(make_fill(f"open-{open_side.value}", open_side, 100.0, quantity=2.0))
                state = portfolio.apply_fill(
                    make_fill(f"reverse-{open_side.value}", reversal_side, reversal_price, quantity=5.0, minute=15)
                )
                position = state.positions["BTCUSDT"]
                self.assertEqual(position.side, expected_side)
                self.assertEqual(position.quantity, 3.0)
                self.assertEqual(position.average_entry_price, reversal_price)
                self.assertEqual(state.realized_pnl, expected_pnl)

    def test_pf_011_and_012_mark_to_market_long_and_short(self):
        cases = [(OrderSide.BUY, 110.0, 20.0), (OrderSide.SELL, 90.0, 20.0)]
        for side, mark_price, expected_unrealized in cases:
            with self.subTest(side=side):
                portfolio = Portfolio()
                portfolio.apply_fill(make_fill(f"mtm-open-{side.value}", side, 100.0, quantity=2.0))
                state = portfolio.mark_to_market(START_TIME + timedelta(minutes=15), {"BTCUSDT": mark_price})
                self.assertEqual(state.unrealized_pnl, expected_unrealized)
                self.assertEqual(state.positions["BTCUSDT"].unrealized_pnl, expected_unrealized)

    def test_pf_013_mark_to_market_changes_no_ledger_values_except_unrealized_and_equity(self):
        portfolio = Portfolio()
        before = portfolio.apply_fill(make_fill("mtm-invariant", OrderSide.BUY, 100.0, fee=2.0))
        after = portfolio.mark_to_market(START_TIME + timedelta(minutes=15), {"BTCUSDT": 120.0})

        self.assertEqual(after.positions["BTCUSDT"].quantity, before.positions["BTCUSDT"].quantity)
        self.assertEqual(after.positions["BTCUSDT"].average_entry_price, before.positions["BTCUSDT"].average_entry_price)
        self.assertEqual(after.realized_pnl, before.realized_pnl)
        self.assertEqual(after.fees_paid, before.fees_paid)
        self.assertEqual(after.unrealized_pnl, 20.0)
        self.assertEqual(after.equity, before.equity + 20.0)

    def test_pf_014_fees_accumulate_without_changing_realized_pnl_or_entry(self):
        portfolio = Portfolio()
        open_state = portfolio.apply_fill(make_fill("fee-open", OrderSide.BUY, 100.0, fee=2.0))
        close_state = portfolio.apply_fill(make_fill("fee-close", OrderSide.SELL, 120.0, fee=3.0, minute=15))

        self.assertEqual(open_state.fees_paid, 2.0)
        self.assertEqual(open_state.realized_pnl, 0.0)
        self.assertEqual(portfolio.account.fees_paid, 5.0)
        self.assertEqual(close_state.realized_pnl, 20.0)
        self.assertEqual(close_state.equity, 10015.0)

    def test_pf_015_duplicate_fill_is_rejected_and_has_no_second_ledger_effect(self):
        portfolio = Portfolio()
        fill = make_fill("duplicate", OrderSide.BUY, 100.0)
        portfolio.apply_fill(fill)

        with self.assertRaises(DuplicateFillError):
            portfolio.apply_fill(fill)
        state = portfolio.get_state(START_TIME + timedelta(minutes=15))
        self.assertEqual(state.positions["BTCUSDT"].quantity, 1.0)
        self.assertEqual(state.realized_pnl, 0.0)

    def test_pf_016_equity_reconciles_to_account_equity_plus_total_unrealized(self):
        portfolio = Portfolio()
        portfolio.apply_fill(make_fill("reconcile-open", OrderSide.BUY, 100.0, quantity=2.0, fee=5.0))
        portfolio.apply_fill(make_fill("reconcile-reduce", OrderSide.SELL, 150.0, fee=0.0, minute=15))
        state = portfolio.mark_to_market(START_TIME + timedelta(minutes=30), {"BTCUSDT": 130.0})

        self.assertEqual(state.realized_pnl, 50.0)
        self.assertEqual(state.unrealized_pnl, 30.0)
        self.assertEqual(state.equity, portfolio.account.equity + state.unrealized_pnl)
        self.assertEqual(state.equity, 10075.0)

    def test_pf_017_mark_to_market_close_transfers_unrealized_to_realized_without_value_creation(self):
        portfolio = Portfolio()
        portfolio.apply_fill(make_fill("transfer-open", OrderSide.BUY, 100.0))
        marked_state = portfolio.mark_to_market(START_TIME + timedelta(minutes=15), {"BTCUSDT": 120.0})
        closed_state = portfolio.apply_fill(make_fill("transfer-close", OrderSide.SELL, 120.0, minute=30))

        self.assertEqual(marked_state.unrealized_pnl, 20.0)
        self.assertEqual(closed_state.unrealized_pnl, 0.0)
        self.assertEqual(closed_state.realized_pnl, 20.0)
        self.assertEqual(marked_state.equity, closed_state.equity)

    def test_pf_018_golden_portfolio_lifecycle(self):
        portfolio = Portfolio()
        portfolio.apply_fill(make_fill("golden-open", OrderSide.BUY, 100.0, quantity=2.0, fee=2.0))
        portfolio.mark_to_market(START_TIME + timedelta(minutes=15), {"BTCUSDT": 110.0})
        portfolio.apply_fill(make_fill("golden-reduce", OrderSide.SELL, 120.0, fee=1.0, minute=30))
        portfolio.mark_to_market(START_TIME + timedelta(minutes=45), {"BTCUSDT": 90.0})
        portfolio.apply_fill(make_fill("golden-reverse", OrderSide.SELL, 90.0, quantity=3.0, fee=3.0, minute=60))
        final_state = portfolio.mark_to_market(START_TIME + timedelta(minutes=75), {"BTCUSDT": 80.0})

        position = final_state.positions["BTCUSDT"]
        self.assertEqual(position.side, PositionSide.SHORT)
        self.assertEqual(position.quantity, 2.0)
        self.assertEqual(position.average_entry_price, 90.0)
        self.assertEqual(final_state.realized_pnl, 10.0)
        self.assertEqual(final_state.fees_paid, 6.0)
        self.assertEqual(final_state.unrealized_pnl, 20.0)
        self.assertEqual(portfolio.account.equity, 10004.0)
        self.assertEqual(final_state.equity, 10024.0)
