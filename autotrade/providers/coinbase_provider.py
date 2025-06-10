import json
import logging
import datetime
import asyncio

from autotrade.settings.secrets import get_secret_key, get_api_key
from autotrade.metrics.metrics import MetricsManager
from autotrade.events.events import Events

from coinbase.websocket import WSClient

class CoinbaseProvider(): 
    def __init__(self, product: str, on_message: callable):
        api_key = get_api_key() 
        api_secret = get_secret_key()
        self.product = product
        self.client = WSClient(api_key=api_key, api_secret=api_secret, on_message=on_message, verbose=True)

    async def start(self):
        await asyncio.sleep(2)
        self.client.open()
        self.client.subscribe([self.product], ["heartbeats" , "level2", "ticker"])
        await self.client.run_forever_with_exception_check_async()
