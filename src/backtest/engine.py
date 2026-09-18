"""
[PURPOSE]: Core Backtest Engine orchestrating simulation components.
[DEPENDENCIES]: core.clock, market_data.loader.
"""

class BacktestEngine:
    """
    [PURPOSE]: Execute backtest run on historical dataset.
    [DEPENDENCIES]: None.
    """
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
