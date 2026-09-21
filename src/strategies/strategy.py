"""
Strategy Protocol interface (`src/strategies/strategy.py`).
"""

from typing import Protocol, runtime_checkable, Union

from src.core.ids import StrategyId
from src.strategies.context import StrategyContext
from src.strategies.signal import Signal


@runtime_checkable
class Strategy(Protocol):
    """
    [PURPOSE]: Protocol contract for Strategy evaluation engines.
    [DEPENDENCIES]: StrategyContext, Signal, StrategyId.
    """

    @property
    def strategy_id(self) -> Union[StrategyId, str]:
        """
        [PURPOSE]: Return unique identifier of the strategy instance.
        """
        ...

    def on_bar(self, context: StrategyContext) -> Signal:
        """
        [PURPOSE]: Evaluate read-only StrategyContext and return directional Signal.
        [DEPENDENCIES]: StrategyContext.
        [ARGS]: context — Immutable StrategyContext container.
        [RETURNS]: Signal value object.
        [SIDE EFFECTS]: Pure method — must NOT mutate context or external state.
        """
        ...
