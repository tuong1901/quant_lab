"""
Fill Model Abstract & Implementation Classes (`src/trading/execution/fill_model.py`).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from src.trading.execution.order import FillId, Order, OrderSide, OrderType, OrderStatus
from src.trading.execution.fill import Fill


class FillModel(ABC):
    """
    [PURPOSE]: Abstract interface converting Order into Fill.
    """
    @abstractmethod
    def simulate_fill(
        self,
        order: Order,
        market_data: Dict[str, float],
        timestamp: datetime,
        slippage_price: Optional[float] = None,
        fee_amount: float = 0.0,
    ) -> Optional[Fill]:
        pass


class OHLCFillModel(FillModel):
    """
    [PURPOSE]: Standard OHLC fill simulation model (Market orders fill at Open/Close price).
    """

    def simulate_fill(
        self,
        order: Order,
        market_data: Dict[str, float],
        timestamp: datetime,
        slippage_price: Optional[float] = None,
        fee_amount: float = 0.0,
    ) -> Optional[Fill]:
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
            return None

        exec_price = slippage_price if slippage_price is not None else market_data.get("open", market_data.get("close", 0.0))

        if order.order_type == OrderType.LIMIT:
            h = market_data.get("high", exec_price)
            l = market_data.get("low", exec_price)
            if order.side == OrderSide.BUY and l > order.price:
                return None
            if order.side == OrderSide.SELL and h < order.price:
                return None
            exec_price = order.price if slippage_price is None else slippage_price

        return Fill(
            fill_id=str(FillId.generate()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=exec_price,
            fee=fee_amount,
            timestamp=timestamp,
        )


class LowerTimeframeReplayFillModel(FillModel):
    """
    [PURPOSE]: Intrabar M1 replay fill model for precise SL/TP evaluation without lookahead bias.
    """

    def simulate_fill(
        self,
        order: Order,
        market_data: Dict[str, float],
        timestamp: datetime,
        slippage_price: Optional[float] = None,
        fee_amount: float = 0.0,
    ) -> Optional[Fill]:
        model = OHLCFillModel()
        return model.simulate_fill(order, market_data, timestamp, slippage_price, fee_amount)
