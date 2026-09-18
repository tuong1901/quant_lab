"""
[PURPOSE]: Performance metrics computation (Sharpe, Sortino, MaxDD, Expectancy).
[DEPENDENCIES]: numpy, pandas.
"""

import numpy as np
import pandas as pd

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, annualization_factor: int = 252) -> float:
    """
    [PURPOSE]: Calculate annualized Sharpe Ratio.
    [DEPENDENCIES]: numpy.
    [ARGS]: returns — daily/bar return series; risk_free_rate — rf; annualization_factor — bars/yr.
    [RETURNS]: Float Sharpe Ratio.
    [SIDE EFFECTS]: None.
    """
    excess_returns = returns - (risk_free_rate / annualization_factor)
    std = excess_returns.std()
    if std == 0 or np.isnan(std):
        return 0.0
    return (excess_returns.mean() / std) * np.sqrt(annualization_factor)

def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    [PURPOSE]: Calculate Maximum Drawdown percentage from Equity Curve.
    [DEPENDENCIES]: pandas.
    [ARGS]: equity_curve — cumulative equity series.
    [RETURNS]: Float Max Drawdown % (e.g. 0.15 for 15%).
    [SIDE EFFECTS]: None.
    """
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return abs(drawdown.min())
