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
    def determine_reference_price(
        self,
        order: Order,
        market_data: Dict[str, float],
    ) -> Optional[float]:
        """
        [PURPOSE]: Decide whether an order is eligible on a bar and return its pre-cost price.
        [DEPENDENCIES]: Called by ExecutionEngine before slippage and fee calculation.
        [ARGS]: order — pending order; market_data — OHLC values for the candidate bar.
        [RETURNS]: Reference price, or None when the order remains pending.
        [SIDE EFFECTS]: None (pure decision).
        """
        pass

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

    def determine_reference_price(
        self,
        order: Order,
        market_data: Dict[str, float],
    ) -> Optional[float]:
        """
        [PURPOSE]: Apply OHLC eligibility rules and choose the order's reference price.
        [DEPENDENCIES]: Called by ExecutionEngine before transaction-cost calculation.
        [ARGS]: order — pending market or limit order; market_data — OHLC values for one bar.
        [RETURNS]: Open/close reference for market orders, limit price for touched limit orders, or None.
        [SIDE EFFECTS]: None (pure decision).
        """
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
            return None

        if order.order_type == OrderType.MARKET:
            return market_data.get("open", market_data.get("close", 0.0))

        high = market_data.get("high", 0.0)
        low = market_data.get("low", 0.0)
        if order.side == OrderSide.BUY and low <= order.price:
            return order.price
        if order.side == OrderSide.SELL and high >= order.price:
            return order.price
        return None

    def simulate_fill(
        self,
        order: Order,
        market_data: Dict[str, float],
        timestamp: datetime,
        slippage_price: Optional[float] = None,
        fee_amount: float = 0.0,
    ) -> Optional[Fill]:
        reference_price = self.determine_reference_price(order, market_data)
        if reference_price is None:
            return None
        exec_price = slippage_price if slippage_price is not None else reference_price

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

    def determine_reference_price(
        self,
        order: Order,
        market_data: Dict[str, float],
    ) -> Optional[float]:
        """
        [PURPOSE]: Delegate current placeholder eligibility logic to the OHLC model.
        [DEPENDENCIES]: Uses OHLCFillModel until lower-timeframe replay is implemented.
        [ARGS]: order — pending order; market_data — current OHLC bar.
        [RETURNS]: Reference price or None when the order remains pending.
        [SIDE EFFECTS]: None (pure decision).
        """
        return OHLCFillModel().determine_reference_price(order, market_data)

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
