"""
[PURPOSE]: Manage simulation time and event clock synchronizers.
[DEPENDENCIES]: core.types.
[ARGS]: N/A.
[RETURNS]: N/A.
[SIDE EFFECTS]: Tracks global system timestamp.
"""

from datetime import datetime

class SimulationClock:
    """
    [PURPOSE]: Causal clock tracking current timestamp in backtests.
    [DEPENDENCIES]: None.
    """
    def __init__(self, start_time: datetime):
        self._current_time = start_time

    def tick(self, new_time: datetime) -> None:
        """
        [PURPOSE]: Advance simulation clock to new timestamp.
        [DEPENDENCIES]: None.
        [ARGS]: new_time — datetime object.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates self._current_time.
        """
        if new_time < self._current_time:
            raise ValueError("Lookahead clock error: Cannot move backwards in time.")
        self._current_time = new_time

    @property
    def current_time(self) -> datetime:
        return self._current_time
