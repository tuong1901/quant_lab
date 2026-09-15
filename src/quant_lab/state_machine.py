"""
State Machine & Trigger Filter Engine for M15 BTCUSDT Pipeline Quant Lab.
Implements 5-stage setup sequence, Equilibrium Premium/Discount bias filtering, rejection wick / engulfing triggers, and stage timeout invalidation.
"""

from typing import Dict, Any, Optional, Tuple


class SetupStateMachine:
    """
    [PURPOSE]: Track setup progression from Stage 0 through Stage 4 entry trigger.
    [DEPENDENCIES]: Used by execution simulator and strategy evaluator.
    """
    def __init__(self, timeout_bars: int = 24):
        self.timeout_bars = timeout_bars
        self.reset_state()
        
    def reset_state(self) -> None:
        """
        [PURPOSE]: Reset state machine back to Stage 0 (Idle/Setup).
        [DEPENDENCIES]: Called on stage timeout, trade exit, or WFO window boundary transition.
        [ARGS]: None.
        [RETURNS]: None.
        [SIDE EFFECTS]: Mutates internal state attributes.
        """
        self.stage = 0
        self.direction: Optional[str] = None
        self.bars_in_stage = 0
        self.entry_price: Optional[float] = None
        self.projected_target: Optional[float] = None
        self.touched_zone: Optional[Dict[str, Any]] = None

    def update_bar(
        self,
        bar: Dict[str, float],
        atr_val: float,
        equilibrium_price: float,
        trigger_candle_type: str,
        buffer_k: float
    ) -> Tuple[int, Optional[str], Optional[float]]:
        """
        [PURPOSE]: Process single candlestick update through state machine logic.
        [DEPENDENCIES]: Calls check_trigger_candle().
        [ARGS]: bar — Candlestick dict.
                atr_val — Wilder RMA ATR value.
                equilibrium_price — Equilibrium price (0.5 Fib mid level).
                trigger_candle_type — Pattern trigger choice.
                buffer_k — ATR buffer multiplier.
        [RETURNS]: Tuple of (current_stage, trade_direction, entry_price_trigger).
        [SIDE EFFECTS]: Increments bars_in_stage, updates self.stage.
        """
        open_p = bar['open']
        high_p = bar['high']
        low_p = bar['low']
        close_p = bar['close']
        
        if self.stage > 0:
            self.bars_in_stage += 1
            if self.bars_in_stage > self.timeout_bars:
                self.reset_state()
                return self.stage, None, None

        buffer = buffer_k * atr_val

        if self.stage == 0:
            if close_p < equilibrium_price:
                self.direction = 'long'
                self.stage = 1
                self.entry_price = close_p
                self.bars_in_stage = 0
            elif close_p > equilibrium_price:
                self.direction = 'short'
                self.stage = 1
                self.entry_price = close_p
                self.bars_in_stage = 0

        elif self.stage == 1:
            self.stage = 2
            self.bars_in_stage = 0
            if self.direction == 'long':
                self.projected_target = self.entry_price + (2.5 * atr_val)
            else:
                self.projected_target = self.entry_price - (2.5 * atr_val)

        elif self.stage == 2:
            target_reached = False
            if self.direction == 'long' and high_p >= (self.projected_target - buffer):
                target_reached = True
            elif self.direction == 'short' and low_p <= (self.projected_target + buffer):
                target_reached = True
                
            if target_reached:
                self.stage = 3
                self.bars_in_stage = 0

        elif self.stage == 3:
            is_triggered = check_trigger_candle(bar, self.direction, trigger_candle_type)
            if is_triggered:
                self.stage = 4
                entry_exec_price = close_p
                direction = self.direction
                self.reset_state()
                return 4, direction, entry_exec_price

        return self.stage, None, None


def check_trigger_candle(bar: Dict[str, float], direction: str, trigger_type: str) -> bool:
    """
    [PURPOSE]: Validate candle pattern trigger at Stage 3.
    [DEPENDENCIES]: Called by SetupStateMachine.update_bar().
    [ARGS]: bar — Candlestick dict.
            direction — Trade direction ('long' or 'short').
            trigger_type — Pattern choice ('rejection_wick', 'engulfing', 'any').
    [RETURNS]: bool — True if trigger met, False otherwise.
    [SIDE EFFECTS]: None (pure function).
    """
    open_p = bar['open']
    high_p = bar['high']
    low_p = bar['low']
    close_p = bar['close']
    
    total_range = high_p - low_p
    if total_range <= 0:
        return False
        
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    
    is_rejection = False
    if direction == 'long':
        is_rejection = (lower_wick / total_range) >= 0.40
    else:
        is_rejection = (upper_wick / total_range) >= 0.40
        
    is_engulfing = False
    if direction == 'long':
        is_engulfing = (close_p > open_p) and ((close_p - open_p) / total_range >= 0.50)
    else:
        is_engulfing = (close_p < open_p) and ((open_p - close_p) / total_range >= 0.50)
        
    if trigger_type == 'rejection_wick':
        return is_rejection
    elif trigger_type == 'engulfing':
        return is_engulfing
    else:
        return is_rejection or is_engulfing
