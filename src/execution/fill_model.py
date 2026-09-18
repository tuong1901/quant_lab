"""
[PURPOSE]: Abstract FillModel interface and concrete implementations (OHLCFillModel, LowerTimeframeReplayFillModel).
[DEPENDENCIES]: abc, dataclasses, datetime, typing, src.execution.order, src.execution.exceptions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from src.execution.order import Order, OrderType, OrderSide
from src.execution.exceptions import FillModelError

@dataclass(frozen=True)
class FillCandidate:
    """
    [PURPOSE]: Immutable candidate fill determined by a FillModel prior to slippage/fee adjustments.
    [DEPENDENCIES]: datetime.
    [ARGS]:
        quantity — Proposed fill quantity.
        price — Theoretical execution fill price.
        timestamp — Timestamp when fill condition was triggered.
        reason — Reason string (e.g. 'MARKET_FILL', 'LIMIT_HIT', 'STOP_LOSS_HIT', 'TAKE_PROFIT_HIT').
    """
    quantity: float
    price: float
    timestamp: datetime
    reason: str = ""

class FillModel(ABC):
    """
    [PURPOSE]: Abstract interface for determining order fills against market observation data.
    """
    @abstractmethod
    def determine_fills(
        self,
        order: Order,
        market_data: Any,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> List[FillCandidate]:
        """
        [PURPOSE]: Determine if and how an order can be filled given market data.
        [DEPENDENCIES]: Order, FillCandidate.
        [ARGS]:
            order — Target Order instance to evaluate.
            market_data — Market data bar(s) or lower timeframe sequence.
            execution_context — Additional context dict.
        [RETURNS]: List of FillCandidate objects.
        """
        pass

class OHLCFillModel(FillModel):
    """
    [PURPOSE]: Single-bar OHLC fill model with deterministic order execution and ambiguity resolution rules.
    [DEPENDENCIES]: FillModel, Order, FillCandidate, FillModelError.
    """
    def __init__(self, market_order_policy: str = "open", ambiguity_policy: str = "pessimistic_sl_first"):
        """
        [ARGS]:
            market_order_policy — 'open' (fill at bar open) or 'close' (fill at bar close).
            ambiguity_policy — 'pessimistic_sl_first' or 'optimistic_tp_first'.
        """
        self.market_order_policy = market_order_policy
        self.ambiguity_policy = ambiguity_policy

    def determine_fills(
        self,
        order: Order,
        market_data: Any,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> List[FillCandidate]:
        if not order.is_active and order.status != order.status.CREATED:
            return []

        # Convert dict or series
        bar = market_data if isinstance(market_data, dict) else market_data.to_dict()
        open_price = float(bar['open'])
        high_price = float(bar['high'])
        low_price = float(bar['low'])
        close_price = float(bar['close'])
        bar_time = bar['timestamp'] if 'timestamp' in bar else bar['time']

        req_qty = order.remaining_quantity
        if req_qty <= 0:
            return []

        # 1. MARKET ORDER
        if order.order_type == OrderType.MARKET:
            fill_price = open_price if self.market_order_policy == "open" else close_price
            return [FillCandidate(quantity=req_qty, price=fill_price, timestamp=bar_time, reason="MARKET_FILL")]

        # 2. LIMIT ORDER
        elif order.order_type == OrderType.LIMIT:
            limit_p = order.limit_price
            if order.side == OrderSide.BUY:
                if low_price <= limit_p:
                    fill_price = min(limit_p, open_price)
                    return [FillCandidate(quantity=req_qty, price=fill_price, timestamp=bar_time, reason="LIMIT_BUY_HIT")]
            elif order.side == OrderSide.SELL:
                if high_price >= limit_p:
                    fill_price = max(limit_p, open_price)
                    return [FillCandidate(quantity=req_qty, price=fill_price, timestamp=bar_time, reason="LIMIT_SELL_HIT")]

        # 3. STOP ORDER (Stop Loss / Take Profit Trigger)
        elif order.order_type == OrderType.STOP:
            stop_p = order.stop_price
            if order.side == OrderSide.BUY:
                if high_price >= stop_p:
                    fill_price = max(stop_p, open_price)
                    return [FillCandidate(quantity=req_qty, price=fill_price, timestamp=bar_time, reason="STOP_BUY_TRIGGERED")]
            elif order.side == OrderSide.SELL:
                if low_price <= stop_p:
                    fill_price = min(stop_p, open_price)
                    return [FillCandidate(quantity=req_qty, price=fill_price, timestamp=bar_time, reason="STOP_SELL_TRIGGERED")]

        return []

class LowerTimeframeReplayFillModel(FillModel):
    """
    [PURPOSE]: Replays lower-timeframe (e.g. M1) bar sequences to resolve intrabar execution order (SL vs TP) deterministically without lookahead.
    [DEPENDENCIES]: FillModel, Order, FillCandidate, OHLCFillModel.
    """
    def __init__(self, base_fill_model: Optional[OHLCFillModel] = None):
        self.single_bar_model = base_fill_model or OHLCFillModel(market_order_policy="open")

    def determine_fills(
        self,
        order: Order,
        market_data: Any,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> List[FillCandidate]:
        """
        [ARGS]:
            market_data — Sequence of lower-timeframe bars (List[Dict] or List[Series]).
        """
        if not isinstance(market_data, (list, tuple)):
            # Fallback to single bar if scalar bar passed
            return self.single_bar_model.determine_fills(order, market_data, execution_context)

        # Sequentially replay lower timeframe bars
        for ltf_bar in market_data:
            candidates = self.single_bar_model.determine_fills(order, ltf_bar, execution_context)
            if candidates:
                # First matching lower-timeframe bar triggers fill, terminate replay
                return candidates

        return []
