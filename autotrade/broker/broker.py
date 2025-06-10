from coinbase.rest.types.orders_types import Order
from coinbase.rest.types.product_types import GetProductResponse
from typing import Tuple, List, Union
from abc import ABC, abstractmethod

from autotrade.types.broker_error import BrokerError
from autotrade.types.pending_order import PendingOrder

class Broker(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_market_order(self, volume: str, cost: str, confidence: float) -> Tuple[Union[PendingOrder,None], Union[BrokerError,None]]:
        pass

    @abstractmethod
    def create_limit_order(self, volume: str, limit_price: str, confidence: float, timeout_sec: int) -> Tuple[Union[PendingOrder,None], Union[BrokerError,None]]:
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Tuple[Union[Order, None], str]:
        pass

    @abstractmethod
    def list_orders(self) ->List[Order]:
        pass

    @abstractmethod
    def get_product_details(self) -> GetProductResponse:
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> Union[BrokerError, None]:
        pass

    @abstractmethod
    def cancel_current_order(self) -> Union[BrokerError, None]:
        pass
