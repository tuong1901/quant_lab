"""
Unit tests for BacktestState audit trail object (`src/backtest/state.py`).
"""

import unittest
from datetime import datetime, timezone

from src.strategies.signal import Signal, SignalAction


class TestBacktestState(unittest.TestCase):
    """
    [PURPOSE]: Verify BacktestState initialization and record storage.
    """

    def test_state_initialization(self):
        """Test creating empty BacktestState container and adding records."""
        from src.engine.backtest.state import BacktestState

        state = BacktestState()
        self.assertEqual(state.bars_processed, 0)
        self.assertEqual(len(state.signals), 0)
        self.assertEqual(len(state.orders), 0)
        self.assertEqual(len(state.fills), 0)
        self.assertEqual(len(state.portfolio_states), 0)

        sig = Signal(timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc), action=SignalAction.LONG)
        state.signals.append(sig)
        state.bars_processed += 1

        self.assertEqual(state.bars_processed, 1)
        self.assertEqual(len(state.signals), 1)


if __name__ == "__main__":
    unittest.main()
