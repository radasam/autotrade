import dateutil.parser
import datetime
import asyncio
import numpy as np

from autotrade.types.order_metrics import OrderMetrics
from autotrade.metrics.metric_values.main import MetricValue
from autotrade.metrics.exporter.prometheus import PrometheusExporter
from autotrade.settings.config import config
from autotrade.exporter.exporter_manager import exporter_manager
from autotrade.events.events import Events
from autotrade.events.event_types import EventType

# 2025-01-12T14:59:32.032976Z
class Orders(MetricValue):
    def __init__(self, product: str, tick_size: float, metrics_exporter: PrometheusExporter, events: Events):
        super().__init__()
        self.product = product
        self.tick_size = tick_size  
        self.metrics_exporter = metrics_exporter
        self.events = events
        self.value = OrderMetrics(buy_volume=0, sell_volume=0, spread=0, imbalance=0, max_buy=0, min_buy=0, max_sell=0, min_sell=0)
        self.order_buys = {}
        self.order_sells = {}
        self.value_lock = asyncio.Lock()
        self.buys_lock = asyncio.Lock()
        self.sells_lock = asyncio.Lock()

    async def get_value(self) -> OrderMetrics:
        async with self.value_lock:
            return self.value
    
    async def update_orders(self, updates, time):
        for update in updates:
            side=update["side"]
            price=float(update["price_level"])
            volume=float(update["new_quantity"])
            # buy
            if side == "bid":
                exporter_manager.add_observation(**{"metric_name":"orders", "side": side, "time":time, "price": price, "volume": volume})
                # we can delete the entry if there is zero volume
                if volume == 0:
                    if price in self.order_buys:
                        async with self.buys_lock:
                            if price == self.value.min_buy:
                                self.value.min_buy = 0
                            if price == self.value.max_buy:
                                self.value.max_buy = 0
                            del self.order_buys[price]
                        continue
                    continue
                async with self.buys_lock:
                    self.order_buys[price] = volume
                continue
            
            exporter_manager.add_observation(**{"metric_name":"orders", "side": side, "time": time, "price": price, "volume": volume})
            # we can delete the entry if there is zero volume
            if volume == 0:
                if price in self.order_sells:
                    async with self.sells_lock:
                        if price == self.value.min_sell:
                            self.value.min_sell = 0
                        if price == self.value.max_sell:
                            self.value.max_sell = 0
                        del self.order_sells[price]
                    continue
                continue
            async with self.sells_lock:
                self.order_sells[price] = volume
            continue

    
    async def update(self,  queue_depth: int, **kwargs):
        async with self.value_lock:
            # print("orders update" + str(kwargs.get("time")))
            orders = kwargs.get("order_updates")
            update_time = dateutil.parser.parse(kwargs.get("time"))
            recieved_time = kwargs.get("recieved")

            self.min_buy = 0
            self.max_buy = 0
            self.min_sell = 0
            self.max_sell = 0

            await self.update_orders(orders, kwargs.get("time"))

            config_value = await config.get_config()
            price_distance_threshold = config_value.price_distance_threshold
            order_size_threshold = config_value.order_size_threshold

            buys = 0
            sells = 0
            buys_copy = {}
            sells_copy = {}

            async with self.buys_lock:    
                buys_copy =  self.order_buys.copy()

            async with self.sells_lock:    
                sells_copy =  self.order_sells.copy()

            np.percentile(list(sells_copy.values()) + list(buys_copy.values()), 50)

            for k, v in buys_copy.items():
                if k < self.value.min_buy or self.value.min_buy == 0:
                    self.value.min_buy = k
                if k > self.value.max_buy:
                    self.value.max_buy = k
            for k, v in sells_copy.items():
                if k < self.value.min_sell or self.value.min_sell == 0:
                    self.value.min_sell = k
                if k > self.value.max_sell:
                    self.value.max_sell = k

            mid_price = (self.value.min_sell + self.value.max_buy) / 2

            for k, v in buys_copy.items():
                ticks_from_mid = abs(k - mid_price) / self.tick_size
                if ticks_from_mid > price_distance_threshold:
                    continue
                if v > order_size_threshold:
                    continue
                buys += k * v

            for k, v in sells_copy.items():
                ticks_from_mid = abs(k - mid_price) / self.tick_size
                if ticks_from_mid > price_distance_threshold:
                    continue
                if v > order_size_threshold:
                    continue
                sells += k * v

            # Check for distance from mid price

            if float(buys + sells) == 0:
                print("no orders")
                return

            self.value.buy_volume = buys
            self.value.sell_volume = sells
            self.value.imbalance = float(buys - sells) / float(buys + sells)
            self.value.spread = self.value.min_sell - self.value.max_buy

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        recieved_lag = now.microsecond - recieved_time
        update_lag = (now - update_time).microseconds

        self.metrics_exporter.gauge_buy_orders.labels(self.product).set(buys)
        self.metrics_exporter.gauge_sell_orders.labels(self.product).set(sells)
        self.metrics_exporter.guage_order_update_lag.labels(self.product).set(update_lag)
        self.metrics_exporter.guage_order_queue_lag.labels(self.product).set(recieved_lag)
        self.metrics_exporter.guage_order_queue_depth.labels(self.product).set(queue_depth)

        # exporter_manager.add_observation(**{"metric_name":"order_buys", "time": kwargs.get("time"), "value": buys})
        # exporter_manager.add_observation(**{"metric_name":"order_sells", "time": kwargs.get("time"), "value": sells})
        self.events.trigger_event(EventType.ORDER_UPDATE, self.value)
        self.events.trigger_event(EventType.ORDER_BOOK_UPDATE, {'buys': buys_copy, 'sells': sells_copy})