from autotrade.events.events import Events
from autotrade.metrics.prometheus import PrometheusExporter
from autotrade.metrics.metric_values.market_price import MarketPrice
from autotrade.metrics.metric_values.orders import Orders
from autotrade.metrics.metric_values.recieved_messages import Recieved_Messages
from autotrade.metrics.metric_values.main import MetricValue
from autotrade.types.order_metrics import OrderMetrics, PriceMetrics

import asyncio


class Metric():
    def __init__(self, name: str, value: MetricValue, threads: int):
        self.name = name
        self.value = value
        self.threads = threads
        pass

    async def _handle_update(self):
        while True:
            try:
                kwargs = self.queue.get_nowait()
                await self.value.update(self.queue.qsize(), **kwargs)
                self.queue.task_done()

            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)
                continue

    def update(self, **kwargs):
        try:
            self.queue.put_nowait(kwargs)
        except asyncio.QueueFull:
            print(f"{self.name} queue full")
            pass

    async def get_value(self):
        return await self.value.get_value()

    async def start(self):
        print(f"Starting metric {self.name}")
        loop = asyncio.get_event_loop()
        self.queue = asyncio.Queue(maxsize=400000, loop=loop)
        consumers = [asyncio.create_task(self._handle_update()) for i in range(self.threads)]
        await asyncio.gather(*consumers)



class Metrics():
    def __init__(self, product: str, metrics_exporter: PrometheusExporter, events: Events):
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.orders = Metric("orders", Orders(product,0.01, metrics_exporter, events), 1)
        self.market_price = Metric("price", MarketPrice(product, metrics_exporter, events), 1)
        self.recieved_messages = Metric("message_info", Recieved_Messages(product, metrics_exporter), 1)

    def update_order(self, order_updates, time: str, recieved: int):
        self.orders.update(**{"order_updates":order_updates, "time":time, "recieved": recieved})

    async def get_order_metrics(self) -> OrderMetrics:
        return await self.orders.get_value()

    def update_market_price(self, price: float, time: str, recieved: int):
        self.market_price.update(**{"price":price, "time":time, "recieved": recieved})

    async def get_price_metrics(self) -> PriceMetrics:
        return await self.market_price.get_value()

    def update_recieved_messages(self, channel: str, update_count: int):
        self.recieved_messages.update(**{"channel": channel, "update_count": update_count})

    async def start(self):
        await asyncio.gather(self.orders.start(), self.market_price.start(), self.recieved_messages.start())

class MetricsManager():
    def __init__(self, product: str, events: Events):
        self.metrics_exporter = PrometheusExporter()
        self.metrics = Metrics(product, self.metrics_exporter, events)


    def update_order(self, order_updates, time: str, recieved: int):
        self.metrics.update_order(order_updates, time, recieved)

    def update_market_price(self, price: float, time: str, recieved: int):
        self.metrics.update_market_price(price, time, recieved)

    def update_recieved_messages(self, channel: str, update_count: int):
        self.metrics.update_recieved_messages(channel, update_count)
    
    def start_metrics_exporter(self):
        self.metrics_exporter.start()

    async def start(self):
        await self.metrics.start()