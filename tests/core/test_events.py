"""
Unit tests for Core Event backbone model (`src/core/events.py`).
"""

import unittest
from datetime import datetime, timezone


class TestCoreEvents(unittest.TestCase):
    """
    [PURPOSE]: Verify Event immutability and deterministic sorting by (timestamp, sequence).
    """

    def test_event_creation_and_immutability(self):
        """Test Event instance creation and frozen immutability constraint."""
        from src.trading.execution.order import EventId, Event

        evt_id = EventId.generate()
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        evt = Event(event_id=evt_id, timestamp=dt, sequence=1)

        self.assertEqual(evt.event_id, evt_id)
        self.assertEqual(evt.timestamp, dt)
        self.assertEqual(evt.sequence, 1)

        with self.assertRaises(AttributeError):
            evt.sequence = 2

    def test_deterministic_event_sorting(self):
        """Test that events are sorted deterministically first by timestamp, then by sequence integer."""
        from src.trading.execution.order import EventId, Event

        dt1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2024, 1, 1, 12, 15, 0, tzinfo=timezone.utc)

        evt_a = Event(event_id=EventId("a"), timestamp=dt1, sequence=2)
        evt_b = Event(event_id=EventId("b"), timestamp=dt1, sequence=1)
        evt_c = Event(event_id=EventId("c"), timestamp=dt2, sequence=1)

        events_list = [evt_c, evt_a, evt_b]
        sorted_events = sorted(events_list, key=lambda e: (e.timestamp, e.sequence))

        self.assertEqual(sorted_events, [evt_b, evt_a, evt_c])


if __name__ == "__main__":
    unittest.main()
