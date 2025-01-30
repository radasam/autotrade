from typing import Dict, List
import threading

from autotrade.events.events import Events
from autotrade.metrics.prometheus import PrometheusExporter
from autotrade.settings.config import ConfigReloader
from autotrade.metrics.metric_values.market_price import MarketPrice
from autotrade.metrics.metric_values.orders import OrderImbalance
from autotrade.metrics.metric_values.recieved_messages import Recieved_Messages
from autotrade.metrics.metric_values.main import MetricValue
from autotrade.types.order_update import OrderUpdate

import asyncio

class Metric():
    def __init__(self, name: str, value: MetricValue, threads: int):
        self.name = name
        self.value = value
        self.threads = threads
        self.lock_queue = False
        pass

    async def _handle_update(self):
        while True:
            try:
                kwargs = self.queue.get_nowait()
                await self.value.update(self.queue.qsize(), **kwargs)
                self.queue.task_done()

            except asyncio.QueueEmpty:
                continue

    def update(self, **kwargs):
        if self.queue.qsize() < 60000 and not self.lock_queue:
            try:
                self.queue.put_nowait(kwargs)
            except asyncio.QueueFull:
                print(f"{self.name} queue full")
                pass
        else:
            self.lock_queue = True

    async def get_value(self):
        return self.value.get_value()
        
    async def _start(self):
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        consumers = [asyncio.create_task(self._handle_update()) for i in range(self.threads)]
        await asyncio.gather(*consumers)

    def start(self):
        self.thread = threading.Thread(target=asyncio.run, args=(self._start(),))
        self.thread.start()


class ProductMetrics():
    def __init__(self, product: str, metrics_exporter: PrometheusExporter):
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.orders = Metric("orders", OrderImbalance(product, metrics_exporter), 1)
        self.market_price = Metric("price", MarketPrice(product, metrics_exporter), 1)
        self.recieved_messages = Metric("message_info", Recieved_Messages(product, metrics_exporter), 1)

    def update_order(self, order_updates: List[OrderUpdate], time: str, recieved: int):
        self.orders.update(**{"order_updates":order_updates, "time":time, "recieved": recieved})

    def update_market_price(self, price: float, time: str, recieved: int):
        self.market_price.update(**{"price":price, "time":time, "recieved": recieved})

    def update_recieved_messages(self, channel: str, update_count: int):
        self.recieved_messages.update(**{"channel": channel, "update_count": update_count})

    def start(self):
        self.market_price.start()
        self.orders.start()
        self.recieved_messages.start()

class Metrics():
    def __init__(self, events: Events):
        self.products : Dict[str, ProductMetrics] = {}
        self.events = events
        self.metrics_exporter = PrometheusExporter()

    def add_product(self, product: str):
        self.products[product] = ProductMetrics(product, self.metrics_exporter)
        self.products[product].start()


    def update_order(self, product: str, order_updates :List[OrderUpdate], time: str, recieved: int):
        if product not in self.products:
            raise ValueError(f"product not initialised in metrics: {product}")
        
        self.products[product].update_order(order_updates, time, recieved)

    def update_market_price(self, product: str, price: float, time: str, recieved: int):
        if product not in self.products:
            raise ValueError(f"product not initialised in metrics: {product}")

        self.products[product].update_market_price(price, time, recieved)

    def update_recieved_messages(self, product: str, channel: str, update_count: int):
        if product not in self.products:
            raise ValueError(f"product not initialised in metrics: {product}")

        self.products[product].update_recieved_messages(channel, update_count)
    
    def start_metrics_exporter(self):
        self.metrics_exporter.start()