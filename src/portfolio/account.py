"""
[PURPOSE]: Account Balance & Equity Tracker.
[DEPENDENCIES]: None.
"""

class Account:
    """
    [PURPOSE]: Track cash balance, equity, and margin reserves.
    [DEPENDENCIES]: None.
    """
    def __init__(self, initial_capital: float):
        self.balance = initial_capital
        self.equity = initial_capital
