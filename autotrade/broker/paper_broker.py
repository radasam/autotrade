import logging
import asyncio
from typing import Dict, Tuple, Union, List
from datetime import datetime, timedelta

from autotrade.metrics.metrics import Metrics
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL
from autotrade.types.broker_error import BrokerError, existing_order_error, insufficient_funds_error, insufficient_product_error, request_error
from autotrade.events.events import Events
from autotrade.events.event_types import EventType
from autotrade.types.pending_order import PendingOrder

class PaperBroker():

    def __init__(self, product: str, balance: float, events: Events):
        self.product = product
        self.curr_price = 0
        self.balance = 0
        self.cash_balance = balance
        self.buys = {}
        self.sells = {}
        self.active_order=None
        self.events = events
        self.price_lock = asyncio.Lock()
        self.order_lock = asyncio.Lock()

    async def start(self):
        await self._order_check_loop()

    async def _order_check_loop(self):
        while True:
            if self.active_order:
                await self.check_current_order()
            await asyncio.sleep(1)

    async def check_current_order(self):
        async with self.order_lock:
            async with self.price_lock:
                if not self.active_order:
                    return
                
                self.try_to_fill_order()
                
                if self.active_order.timeout_at < datetime.now() and self.active_order.status != "CANCELLED" and self.active_order.status != "FILLED":
                    self.active_order.status = "CANCELLED"
                    logging.info(f"Order {self.active_order} is cancelled due to timeout")

                if self.active_order.status == 'FILLED':
                    filled_volume = self.active_order.filled_size
                    avg_filled_price = self.active_order.avg_filled_price
                    side = self.active_order.side
                    self.balance += filled_volume if side == ORDER_BUY else -1 * filled_volume
                    self.cash_balance -= filled_volume * avg_filled_price if side == ORDER_BUY else -1 * filled_volume * avg_filled_price 

                    self.events.trigger_event(EventType.ORDER_FILLED, self.active_order.model_dump())
                    logging.info(f"Order {self.active_order} is filled")
                    self.active_order = None
                    return
                if self.active_order.status == 'CANCELLED':
                    filled_volume = self.active_order.filled_size
                    avg_filled_price = self.active_order.avg_filled_price
                    side = self.active_order.side
                    self.balance += filled_volume if side == ORDER_BUY else -1 * filled_volume
                    self.cash_balance -= filled_volume * avg_filled_price if side == ORDER_BUY else -1 * filled_volume * avg_filled_price

                    self.events.trigger_event(EventType.ORDER_CANCELLED, self.active_order.model_dump())
                    self.active_order = None
                    logging.info(f"Order {self.active_order} is cancelled")
                    return


    async def update_price(self, price: float):
        async with self.price_lock:
            self.curr_price = price

    async def update_order_book(self, values: Dict[str,Dict[float, str]]):
        async with self.order_lock:
            self.buys = values.get("buys")
            self.sells = values.get("sells")

            if self.active_order:
                if self.active_order.status == "FILLED":
                    return
                
                if self.active_order.timeout_at < datetime.now() and self.active_order.status != "CANCELLED" and self.active_order.status != "FILLED":
                    logging.info(f"Order {self.active_order} is cancelled due to timeout")
                    self.active_order.status = "CANCELLED"
                    return

                self.try_to_fill_order()


    def try_to_fill_order(self) -> None:
        order_volume =  self.active_order.volume
        order_price = self.active_order.price 
        order_side = self.active_order.side
        volume_filled = self.active_order.filled_size
        avg_price = self.active_order.avg_filled_price

        if self.active_order.status == "FILLED":
            return
        
        if self.active_order.filled_size > 0:
            return


        logging.info(f"Trying to fill order {self.active_order} with volume {order_volume} and price {order_price}")

        orders = self.sells if order_side == ORDER_BUY else self.buys
        prices = list(orders.keys())

        if order_side == ORDER_SELL:
            prices.sort(reverse=True)


        if not orders:
            return 0, 0, False
        for p in prices:
            if order_side == ORDER_BUY:
                if p > order_price:
                    return avg_price, volume_filled, False
            else:
                if p < order_price:
                    return avg_price, volume_filled, False
                
            delta_volume = min(order_volume - volume_filled, orders[p])
            
            avg_price = ((avg_price * volume_filled) + (p * delta_volume)) / (volume_filled + delta_volume)
            volume_filled += delta_volume
            if volume_filled >= order_volume:
                self.active_order.status = "FILLED"
                self.active_order.filled_size= volume_filled
                self.active_order.avg_filled_price = avg_price
                logging.info(f"Order {self.active_order} is filled")
                return
            if volume_filled > 0:
                self.active_order.filled_size = volume_filled
                self.active_order.avg_filled_price = avg_price
                logging.info(f"Order {self.active_order} is partially filled")
                return

    async def create_market_order(self, volume: str, confidence: float) -> Tuple[Union[PendingOrder, None], Union[BrokerError,None]]:
        async with self.order_lock:
            side = None

            if self.active_order:
                return None, existing_order_error(self.active_order)

            if float(volume) * self.curr_price > self.cash_balance and side == ORDER_BUY:
                return None, insufficient_funds_error(self.product, volume, self.curr_price, self.cash_balance)
            
            if float(volume) > self.balance and side == ORDER_SELL:
                return None, insufficient_product_error(self.product, volume, self.balance)
            
            if float(volume) > 0:
                side = ORDER_BUY
            else:
                side = ORDER_SELL

            new_order = PendingOrder(
                volume=abs(float(volume)),
                price=self.curr_price,
                side=side,
                status="FILLED",
                order_id="dummy_order_id",
                client_order_id="dummy_client_order_id",
                timeout_at=None,
                confidence=confidence
            )

            self.active_order = new_order

            return new_order, None
    
    async def create_limit_order(self, volume: str, limit_price: str, confidence: float, timeout_sec: int) -> Tuple[Union[PendingOrder, None], Union[BrokerError,None]]:
        async with self.order_lock:
            side = None

            if self.active_order:
                return None, existing_order_error(self.active_order)
            
            if float(volume) > 0:
                side = ORDER_BUY
            else:
                side = ORDER_SELL
            
            if float(volume) * float(limit_price) > self.cash_balance and side == ORDER_BUY:
                return None, insufficient_funds_error(self.product, float(volume), float(limit_price), self.cash_balance)

            if float(volume) * -1 > self.balance  and side == ORDER_SELL:
                return None, insufficient_product_error(self.product, volume, self.balance)


            timeout_at = datetime.now() + timedelta(seconds=timeout_sec)

            new_order = PendingOrder(
                volume=abs(float(volume)),
                price=float(limit_price),
                side=side,
                status="OPEN",
                order_id="dummy_order_id",
                client_order_id="dummy_client_order_id",
                timeout_at=timeout_at,
                confidence=confidence
            )

            self.active_order = new_order   

            logging.info(f"Created limit order {self.active_order}")

            self.try_to_fill_order()

            return new_order, None

    def cancel_order(self, order_id: str) -> Union[BrokerError, None]:
        """
        Paper broker assumes we dont make multiple orders at the same time
        so we can just cancel the current order
        """
        if not self.active_order:
            return None
        self.active_order = None
        return None
    
    async def cancel_current_order(self) -> Union[BrokerError, None]:
        async with self.order_lock:
            if not self.active_order:
                return None
            self.active_order = None
            return None
    