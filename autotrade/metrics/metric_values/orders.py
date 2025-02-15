import dateutil.parser
import datetime
import threading
from typing import List

from autotrade.metrics.metric_values.main import MetricValue
from autotrade.metrics.prometheus import PrometheusExporter
from autotrade.settings.config import config
from autotrade.types.order_update import OrderUpdate
from autotrade.exporter.exporter_manager import exporter_manager

# 2025-01-12T14:59:32.032976Z

class OrderImbalance(MetricValue):
    def __init__(self, product: str, metrics_exporter: PrometheusExporter):
        super().__init__()
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.imbalance = 0
        self.order_buys = {}
        self.order_sells = {}
        self.min_sell = 0
        self.max_buy = 0
        self.imbalance = 0
        self.buys_lock = threading.Lock()
        self.sells_lock = threading.Lock()

    def get_value(self):
        return self.imbalance
    
    def update_orders(self, updates):
        for update in updates:
            side=update["side"]
            price=float(update["price_level"])
            volume=float(update["new_quantity"])
            # buy
            if side == "bid":
                if price > self.max_buy:
                    self.max_buy = price

                # we can delete the entry if there is zero volume
                if volume == 0:
                    if price in self.order_buys:
                        with self.buys_lock:
                            del self.order_buys[price]
                        continue
                with self.buys_lock:
                    self.order_buys[price] = volume
                continue
            
            # sell
            
            if price < self.min_sell:
                self.min_sell = price

            # we can delete the entry if there is zero volume
            if volume == 0:
                if price in self.order_sells:
                    with self.sells_lock:
                        del self.order_sells[price]
                    continue
            with self.sells_lock:
                self.order_sells[price] = volume
            continue

    
    async def update(self,  queue_depth: int, **kwargs):
        # side: str, price: float, volume: float
        orders = kwargs.get("order_updates")
        update_time = dateutil.parser.parse(kwargs.get("time"))
        recieved_time = kwargs.get("recieved")

        self.update_orders(orders)

        config_value = await config.get_config()
        percentile = config_value.order_cutoff_percentile

        buys = 0
        sells = 0
        buys_copy = {}
        sells_copy = {}

        with self.buys_lock:    
            buys_copy =  self.order_buys.copy()

        with self.sells_lock:    
            sells_copy =  self.order_sells.copy()

        for k, v in buys_copy.items():
            if k > self.min_sell * (1 - percentile):
                buys += k * v

        for k, v in sells_copy.items():
            if k < self.max_buy  * (1 + percentile):
                sells += k * v

        self.imbalance = buys - sells

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        recieved_lag = now.microsecond - recieved_time
        update_lag = (now - update_time).microseconds

        self.metrics_exporter.gauge_buy_orders.labels(self.product).set(buys)
        self.metrics_exporter.gauge_sell_orders.labels(self.product).set(sells)
        self.metrics_exporter.guage_order_update_lag.labels(self.product).set(update_lag)
        self.metrics_exporter.guage_order_queue_lag.labels(self.product).set(recieved_lag)
        self.metrics_exporter.guage_order_queue_depth.labels(self.product).set(queue_depth)

        exporter_manager.add_observation(**{"metric_name":"order_buys", "time": kwargs.get("time"), "value": buys})
        exporter_manager.add_observation(**{"metric_name":"order_sells", "time": kwargs.get("time"), "value": sells})
