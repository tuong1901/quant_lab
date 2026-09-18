"""
[PURPOSE]: Causal Event Loop Dispatcher.
[DEPENDENCIES]: core.events.
"""

class EventLoop:
    """
    [PURPOSE]: Sequential event processing loop for backtests.
    [DEPENDENCIES]: None.
    """
    def __init__(self):
        self.queue = []

    def push(self, event):
        self.queue.append(event)
