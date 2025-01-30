import threading
import asyncio

from autotrade.markets.market_socket import MarketSocket
from autotrade.metrics.metrics import Metrics
from autotrade.events.events import Events
from autotrade.settings.config import config

class Engine():

    def __init__(self, product: str):
        self.loop = asyncio.get_event_loop()
        self.product = product
        self.event_handler = Events()
        self.metrics = Metrics(self.event_handler)
        self.markets_socket = MarketSocket(product, self.metrics, self.event_handler)
        self.event_handler.add_handler("check_action", "orders_updated", self.on_orders_update)


    def start(self):
        self.event_handler.start()
        self.metrics.start_metrics_exporter()
        self.metrics.add_product(self.product)
        config.start()
        self.markets_socket.start()


    def on_orders_update(self):
        print("orders_updated")