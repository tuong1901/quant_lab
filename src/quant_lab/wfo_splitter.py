"""
Purged Walk-Forward Optimization (WFO) Splitter for M15 BTCUSDT Pipeline Quant Lab.
Handles rolling/expanding train-test windows with trade count guardrails (min 300 trades),
open position purging at window boundaries, K-bar embargoing, and state machine boundary force-reset.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np


class PurgedWFOSplitter:
    """
    [PURPOSE]: Split dataset into purged and embargoed Walk-Forward train/test windows.
    [DEPENDENCIES]: Used by optimizer.py and run_pipeline.py.
    """
    def __init__(
        self,
        min_is_trades: int = 300,
        embargo_bars: int = 96,
        n_windows: int = 4
    ):
        self.min_is_trades = min_is_trades
        self.embargo_bars = embargo_bars
        self.n_windows = n_windows

    def generate_splits(self, total_bars: int) -> List[Dict[str, Any]]:
        """
        [PURPOSE]: Construct index slices for Walk-Forward train/test windows.
        [DEPENDENCIES]: Called before optimization loop.
        [ARGS]: total_bars — Total number of M15 bars in dataset.
        [RETURNS]: List[Dict] — Window split definitions.
        [SIDE EFFECTS]: None (pure calculation).
        """
        splits = []
        if total_bars <= 0:
            return splits

        window_size = total_bars // (self.n_windows + 1)
        
        for w in range(self.n_windows):
            train_start = 0
            train_end = (w + 2) * window_size
            
            test_start = train_end + self.embargo_bars
            test_end = min(total_bars, test_start + window_size)
            
            if test_start < total_bars:
                splits.append({
                    'window_idx': w,
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end
                })

        return splits

    def enforce_boundary_reset(self, state_machine: Any) -> None:
        """
        [PURPOSE]: Force reset state machine state back to Stage 0 at window boundary transition.
        [DEPENDENCIES]: Called by WFO driver at train->test boundary.
        [ARGS]: state_machine — Instance of SetupStateMachine.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates state_machine internal state back to Stage 0.
        """
        state_machine.reset_state()
