"""
[PURPOSE]: ATR Ratchet Exit Module (`src/strategies/atr_ratchet.py`).
[DEPENDENCIES]: typing.
"""

from typing import Optional


class ATRRatchetExit:
    """
    [PURPOSE]: Maintain and update ATR Ratchet trailing stop level for active position.
    [DEPENDENCIES]: Used by strategy and execution simulator.
    """
    def __init__(self, multiplier: float = 3.0):
        self.multiplier = multiplier
        self.active_stop: Optional[float] = None
        self.is_activated = False

    def initialize_stop(
        self,
        entry_price: float,
        direction: str,
        atr_val: float,
        activation_trigger: str
    ) -> float:
        """
        [PURPOSE]: Set initial stop loss level upon position entry.
        """
        initial_distance = self.multiplier * atr_val
        if direction == 'long':
            self.active_stop = entry_price - initial_distance
        else:
            self.active_stop = entry_price + initial_distance
            
        if activation_trigger in ('at_1R', 'at_target_zone'):
            self.is_activated = True
        else:
            self.is_activated = False
            
        return self.active_stop

    def update_ratchet(
        self,
        high_price: float,
        low_price: float,
        close_price: float,
        direction: str,
        atr_val: float,
        entry_price: float,
        activation_trigger: str
    ) -> float:
        """
        [PURPOSE]: Update trailing ratchet stop loss level for current bar.
        """
        if self.active_stop is None:
            self.initialize_stop(entry_price, direction, atr_val, activation_trigger)
            return self.active_stop

        initial_risk = self.multiplier * atr_val
        if not self.is_activated:
            if direction == 'long':
                profit_distance = high_price - entry_price
            else:
                profit_distance = entry_price - low_price
                
            if activation_trigger == 'at_1R' and profit_distance >= initial_risk:
                self.is_activated = True
            elif activation_trigger == 'at_1.5R' and profit_distance >= (1.5 * initial_risk):
                self.is_activated = True
            elif activation_trigger == 'at_2R' and profit_distance >= (2.0 * initial_risk):
                self.is_activated = True
            elif activation_trigger == 'at_target_zone':
                self.is_activated = True

        if self.is_activated:
            ratchet_offset = self.multiplier * atr_val
            if direction == 'long':
                up_bound = high_price - ratchet_offset
                self.active_stop = max(self.active_stop, up_bound)
            else:
                dn_bound = low_price + ratchet_offset
                self.active_stop = min(self.active_stop, dn_bound)
                
        return self.active_stop
