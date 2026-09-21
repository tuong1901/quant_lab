"""
Unit tests for Signal value object and SignalAction enum (`src/strategies/signal.py`).
"""

import unittest
from datetime import datetime, timezone


class TestSignal(unittest.TestCase):
    """
    [PURPOSE]: Verify Signal value object creation, immutability, and SignalAction enum rules.
    """

    def test_signal_action_enum(self):
        """Test SignalAction values (HOLD, LONG, SHORT)."""
        from src.strategies.signal import SignalAction

        self.assertEqual(SignalAction.HOLD.value, "HOLD")
        self.assertEqual(SignalAction.LONG.value, "LONG")
        self.assertEqual(SignalAction.SHORT.value, "SHORT")

    def test_signal_creation_and_immutability(self):
        """Test Signal instantiation and frozen immutability."""
        from src.strategies.signal import Signal, SignalAction

        now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        sig = Signal(timestamp=now, action=SignalAction.LONG, strategy_id="ema_cross_v1")

        self.assertEqual(sig.timestamp, now)
        self.assertEqual(sig.action, SignalAction.LONG)
        self.assertEqual(sig.strategy_id, "ema_cross_v1")

        with self.assertRaises(AttributeError):
            sig.action = SignalAction.SHORT  # Read-only frozen dataclass


if __name__ == "__main__":
    unittest.main()
