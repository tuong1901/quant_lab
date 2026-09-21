"""
Reference EMA Crossover Strategy implementation (`src/strategies/ema.py`).
"""

from typing import Optional, Union

from src.core.ids import StrategyId
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal, SignalAction


class EMAStrategy:
    """
    [PURPOSE]: Minimal reference EMA crossover strategy for validating Strategy Contract.
    [DEPENDENCIES]: StrategyContext, Signal, SignalAction, StrategyId.
    [ARGS]:
        fast_period — Fast EMA lookback window (default 20).
        slow_period — Slow EMA lookback window (default 50).
        strategy_id — Optional strategy identifier override.
    [RETURNS]: EMAStrategy instance.
    [SIDE EFFECTS]: None (pure stateless evaluation).
    """

    def __init__(
        self,
        fast_period: int = 20,
        slow_period: int = 50,
        strategy_id: Optional[Union[StrategyId, str]] = None,
    ) -> None:
        """
        [PURPOSE]: Initialize EMAStrategy parameters.
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self._strategy_id = strategy_id or f"ema_{fast_period}_{slow_period}"

    @property
    def strategy_id(self) -> Union[StrategyId, str]:
        """
        [PURPOSE]: Get strategy identifier.
        """
        return self._strategy_id

    def on_bar(self, context: StrategyContext) -> Signal:
        """
        [PURPOSE]: Evaluate context features for EMA crossover and return Signal.
        [DEPENDENCIES]: Reads features dict from StrategyContext.
        [ARGS]: context — StrategyContext object containing timestamp & features.
        [RETURNS]: Signal with action LONG, SHORT, or HOLD.
        [SIDE EFFECTS]: None (pure method).
        """
        fast_key = f"ema{self.fast_period}"
        slow_key = f"ema{self.slow_period}"

        fast_val = context.features.get(fast_key)
        slow_val = context.features.get(slow_key)

        if fast_val is None or slow_val is None or fast_val == slow_val:
            action = SignalAction.HOLD
        elif fast_val > slow_val:
            action = SignalAction.LONG
        else:
            action = SignalAction.SHORT

        return Signal(
            timestamp=context.timestamp,
            action=action,
            strategy_id=self.strategy_id,
        )
