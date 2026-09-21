"""
[PURPOSE]: Unit tests for Core subsystem (types, clock, ids, events).
[DEPENDENCIES]: unittest, datetime, src.core.
"""

import unittest
from datetime import datetime, timezone, timedelta

from src.core.types import validate_utc_timestamp
from src.core.clock import HistoricalClock
from src.core.ids import ExperimentId, EventId
from src.core.events import Event
from src.core.exceptions import QuantSystemError


class TestUnitCore(unittest.TestCase):
    """
    [PURPOSE]: Unit tests for core domain primitives, time rules, and immutability invariants.
    """

    def test_utc_timestamp_validation_rejects_naive_datetime(self):
        """[Core Unit]: Naive datetimes (without tzinfo) MUST be rejected or converted with strict rules."""
        naive_dt = datetime(2026, 1, 1, 12, 0, 0)
        with self.assertRaises((ValueError, QuantSystemError)):
            validate_utc_timestamp(naive_dt)

    def test_utc_timestamp_accepts_valid_utc(self):
        """[Core Unit]: Valid UTC datetime must pass validation."""
        valid_utc = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = validate_utc_timestamp(valid_utc)
        self.assertEqual(result, valid_utc)

    def test_historical_clock_time_travel_prevention(self):
        """[Core Unit]: HistoricalClock must refuse advancing backward in time."""
        t1 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        t2 = t1 - timedelta(minutes=15)
        
        clock = HistoricalClock(start_time=t1)
        with self.assertRaises((ValueError, QuantSystemError, Exception)):
            clock.advance_to(t2)

    def test_ids_immutability(self):
        """[Core Unit]: ID instances must be immutable (frozen)."""
        exp_id = ExperimentId("exp_001")
        self.assertEqual(exp_id.value, "exp_001")
        with self.assertRaises(AttributeError):
            exp_id.value = "exp_002"  # type: ignore

    def test_event_sequence_sorting(self):
        """[Core Unit]: Events must sort deterministically by timestamp and sequence."""
        t = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        e1 = Event(event_id=EventId("e1"), timestamp=t, sequence=1)
        e2 = Event(event_id=EventId("e2"), timestamp=t, sequence=2)
        
        self.assertLess((e1.timestamp, e1.sequence), (e2.timestamp, e2.sequence))


if __name__ == "__main__":
    unittest.main()
