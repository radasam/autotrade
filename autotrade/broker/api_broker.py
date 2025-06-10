import uuid
from coinbase.rest import RESTClient
from coinbase.rest.types.orders_types import Order, CreateOrderResponse
from coinbase.rest.types.product_types import GetProductResponse
from typing import Tuple, List, Union
import datetime
import asyncio
import logging

from autotrade.settings.secrets import get_api_key, get_secret_key
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL, get_coinbase_api_base_url
from autotrade.types.broker_error import BrokerError, existing_order_error, insufficient_funds_error, insufficient_product_error, request_error

class APIBroker():
    
    def __init__(self, product: str):
        self.product = product
        self.client = RESTClient(get_api_key(), get_secret_key(), base_url=get_coinbase_api_base_url())
        self.account_id = None
        self.balance = 0.0
        self.cash_account_id = None
        self.cash_balance = 0.0
        self.init_accounts()
        self.active_order = None

    async def start(self):
        await self._order_check_loop()

    async def _order_check_loop(self):
        while True:
            if self.active_order:
                self.check_current_order()
            asyncio.sleep(1)

    def get_product_details(self) -> GetProductResponse:
        resp = self.client.get_product(self.product)

        return resp

    def check_current_order(self):
                order, err = self.get_order(self.active_order)
                if err:
                    return
                if not order:
                    return
                if order.status == 'FILLED':
                    logging.info(f"Order {self.active_order} is {order.status} side:{order.side} size:{order.filled_size} price:{order.average_filled_price}")
                    self.active_order = None
                    self.update_balances()
                    return
                if order.status == 'CANCELED':
                    logging.info(f"Order {self.active_order} is {order.status} side:{order.side}")
                    self.active_order = None
                    self.update_balances()
                    return
                
                logging.info(f"Order {self.active_order} is {order.status} side:{order.side}")
                
    def init_accounts(self):
        resp = self.client.get_accounts(limit=100)
        for account in resp.accounts:
            if account.currency == self.product.split('-')[0]:
                self.account_id = account.uuid
                self.balance = float(account.available_balance.get('value'))
            if account.currency ==self.product.split('-')[1]:
                self.cash_account_id = account.uuid
                self.cash_balance = float(account.available_balance.get('value'))

        if not self.account_id:
            raise Exception(f"Failed to find account for {self.product.split('-')[0]}")
        if not self.cash_account_id:
            raise Exception(f"Failed to find account for {self.product.split('-')[1]}")

    def get_balance(self, account_id: str)-> Tuple[Union[float,None], Union[BrokerError,None]]:
        resp = self.client.get_account(account_id)

        if resp.account:
            return float(resp.account.available_balance.value), None
        
        return None, request_error(f"Failed to get balance for account {account_id}")

    def update_balances(self) -> Union[str,None]: 
        balance, err = self.get_balance(self.account_id)
        if err:
            return err
        self.balance = balance

        cash_balance, err = self.get_balance(self.cash_account_id)
        if err:
            return err
        self.cash_balance = cash_balance

    def create_market_order(self, volume: str, cost: str) -> Tuple[Union[str,None], Union[str,None], Union[BrokerError,None]]:
        side = None

        if self.active_order:
            return None, None, existing_order_error(self.active_order)
        
        if float(volume) > 0:
            side = ORDER_BUY
        else:
            side = ORDER_SELL   

        resp: CreateOrderResponse = None
        client_order_id=uuid.uuid4().hex

        if side == ORDER_BUY:
            if float(cost) > self.cash_balance:
                return None, None, insufficient_funds_error(self.product, volume, cost)
            resp = self.client.market_order(client_order_id=client_order_id, product_id=self.product, side=side, quote_size=cost)
        else:
            if float(volume) > self.balance:
                return None, None, insufficient_product_error(self.product, volume)
            resp = self.client.market_order(client_order_id=client_order_id, product_id=self.product, side=side, base_size=volume)

        if resp.success:
            self.active_order = resp.success_response.get('order_id')
            return client_order_id, self.active_order, None
        
        if resp.failure_reason:
            return None, None, request_error( f"Failed to create order: {resp.failure_reason}")
        
        if resp.error_response:
            return None, None, request_error(f"Error creating order: {resp.error_response.error} {resp.error_response.error_details}")


    def create_limit_order(self, volume: str, limit_price: str, timeout_sec: int) -> Tuple[Union[str,None], Union[str,None], Union[BrokerError,None]]:
        side = None

        if self.active_order:
            return None, None, existing_order_error(self.active_order)
        
        if float(volume) > 0:
            side = ORDER_BUY
        else:
            side = ORDER_SELL

        client_order_id = uuid.uuid4().hex
        cancel_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout_sec)
        cancel_time_str = cancel_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        if side == ORDER_BUY:
            if float(limit_price) * float(volume) > self.cash_balance:
                return None, None, insufficient_funds_error(self.product, volume, limit_price)
        else:
            if float(volume) > self.balance:
                return None, None, insufficient_product_error(self.product, volume)

        resp : CreateOrderResponse = self.client.limit_order_gtd(client_order_id=client_order_id, product_id=self.product, side=side, limit_price=limit_price, base_size=volume, end_time=cancel_time_str)

        if resp.success:
            self.active_order = resp.success_response.get('order_id')
            return client_order_id, self.active_order, None
        
        if resp.failure_reason:
            return None, None, request_error(f"Failed to create order: {resp.failure_reason}")
        
        if resp.error_response:
            return None, None, request_error(f"Error creating order: {resp.error_response.error} {resp.error_response.error_details}")
        
    def list_orders(self) -> List[Order]:
        return self.client.list_orders()


    def get_order(self, order_id: str) -> Tuple[Union[Order,None], Union[BrokerError,None]]:
        resp = self.client.get_order(order_id)

        if resp.order:
            return resp.order

        return None, request_error(f"Failed to get order")
    
    
    def cancel_order(self, order_id: str) -> Union[BrokerError,None]:
        resp = self.client.cancel_orders([order_id])

        # were cancelling a single order so we should only get one response
        result = resp.results[0]

        if result.success:
            self.active_order = None
            return None
        
        if result.failure_reason:
            return request_error(f"Failed to cancel order: {result.failure_reason}")
        
    def cancel_current_order(self) -> Union[BrokerError,None]:
        if self.active_order:
            return self.cancel_order(self.active_order)
