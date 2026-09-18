"""
[PURPOSE]: Fee models for calculating transaction commission costs.
[DEPENDENCIES]: abc, typing, src.execution.order, src.execution.exceptions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.execution.order import Order, OrderType
from src.execution.exceptions import FeeError

class FeeModel(ABC):
    """
    [PURPOSE]: Abstract base class for trade fee models.
    """
    @abstractmethod
    def calculate(
        self,
        order: Order,
        fill_price: float,
        fill_quantity: float,
        is_maker: bool = False
    ) -> float:
        """
        [PURPOSE]: Calculate commission fee for an executed fill.
        [DEPENDENCIES]: Order.
        [ARGS]:
            order — Target Order.
            fill_price — Executed fill price.
            fill_quantity — Executed fill quantity.
            is_maker — Boolean indicating if order was executed as Maker.
        [RETURNS]: Fee amount float.
        """
        pass

class PercentageFeeModel(FeeModel):
    """
    [PURPOSE]: Basis points percentage fee model (differentiating Maker vs Taker fees).
    [DEPENDENCIES]: FeeModel, Order, OrderType.
    """
    def __init__(self, maker_bps: float = 2.0, taker_bps: float = 4.0):
        """
        [ARGS]:
            maker_bps — Maker fee in basis points (default 2 bps = 0.02%).
            taker_bps — Taker fee in basis points (default 4 bps = 0.04%).
        """
        self.maker_bps = maker_bps
        self.taker_bps = taker_bps

    def calculate(
        self,
        order: Order,
        fill_price: float,
        fill_quantity: float,
        is_maker: bool = False
    ) -> float:
        if fill_price <= 0 or fill_quantity <= 0:
            raise FeeError(f"Fill price ({fill_price}) and quantity ({fill_quantity}) must be positive.")

        # If order type is LIMIT and is_maker is True, use maker_bps, else taker_bps
        bps = self.maker_bps if (is_maker or order.order_type == OrderType.LIMIT) else self.taker_bps
        notional_value = fill_price * fill_quantity
        return notional_value * (bps / 10000.0)
