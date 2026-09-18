"""
[PURPOSE]: Fitness Evaluator function (Overfit-penalized score).
[DEPENDENCIES]: None.
"""

def evaluate_fitness(sharpe: float, expectancy: float, max_dd: float, n_trades: int) -> float:
    """
    [PURPOSE]: Compute holistic Fitness Score balancing return vs risk and trade count penalty.
    [DEPENDENCIES]: None.
    [ARGS]: sharpe — Sharpe Ratio; expectancy — Expectancy per trade; max_dd — Max Drawdown %; n_trades — trade count.
    [RETURNS]: Float fitness score.
    [SIDE EFFECTS]: None.
    """
    if n_trades < 30 or max_dd > 0.35:
        return -100.0  # Heavy penalty for under-sampled or high-drawdown strategy
    return sharpe * 2.0 + expectancy * 1.5 - max_dd * 3.0
