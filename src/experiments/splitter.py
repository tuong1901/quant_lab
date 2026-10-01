"""
[PURPOSE]: Purged Walk-Forward Optimization (WFO) Splitter (`src/experiments/splitter.py`).
[DEPENDENCIES]: typing.
"""

from typing import List, Dict, Any


class PurgedWFOSplitter:
    """
    [PURPOSE]: Split dataset into purged and embargoed Walk-Forward train/test windows.
    [DEPENDENCIES]: Used by experiment optimization pipeline.
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
        """
        if hasattr(state_machine, 'reset_state'):
            state_machine.reset_state()
