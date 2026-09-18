"""
[PURPOSE]: Aggregate and rank results from 100-1000 strategy runs.
[DEPENDENCIES]: pandas.
"""

import pandas as pd
from typing import List, Dict, Any

def rank_batch_results(results: List[Dict[str, Any]], sort_by: str = "sharpe") -> pd.DataFrame:
    """
    [PURPOSE]: Convert batch results into ranked pandas DataFrame.
    [DEPENDENCIES]: pandas.
    [ARGS]: results — list of result dicts; sort_by — metric key to rank by.
    [RETURNS]: Ranked pandas DataFrame.
    [SIDE EFFECTS]: None.
    """
    df = pd.DataFrame(results)
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=False)
    return df
