"""
[PURPOSE]: Causal guardrails preventing lookahead bias in feature calculation.
[DEPENDENCIES]: pandas.
"""

import pandas as pd

def enforce_causal_shift(series: pd.Series, shift_bars: int = 1) -> pd.Series:
    """
    [PURPOSE]: Enforce strict causal lag on signals or features.
    [DEPENDENCIES]: None.
    [ARGS]: series — pandas Series; shift_bars — number of bars to lag.
    [RETURNS]: Shifted pandas Series.
    [SIDE EFFECTS]: None.
    """
    return series.shift(shift_bars)
