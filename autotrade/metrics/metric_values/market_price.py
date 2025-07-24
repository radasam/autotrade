from collections import deque
import dateutil.parser
import datetime
import asyncio

from autotrade.types.order_metrics import PriceMetrics
from autotrade.types.time_buffer import TimeBuffer
from autotrade.metrics.metric_values.main import MetricValue
from autotrade.metrics.exporter.prometheus import PrometheusExporter
from autotrade.exporter.exporter_manager import exporter_manager
from autotrade.events.events import Events
from autotrade.events.event_types import EventType

class MarketPrice(MetricValue):
    def __init__(self, product: str, metrics_exporter: PrometheusExporter, events: Events):
        super().__init__()
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.events = events
        self.value = PriceMetrics()
        self.value_lock = asyncio.Lock()
        self.long_buffer = TimeBuffer(capacity=1000000, max_age=600)  # Buffer to store the last 1000 prices for averaging
        self.short_buffer = TimeBuffer(capacity=1000, max_age=60)  # Buffer to store the last 100 prices for averaging
        self.atr_buffer = deque(maxlen=14)  # Buffer for ATR calculations, if needed

    async def get_value(self) -> float:
        async with self.value_lock:
            return self.value
        
    async def update(self, queue_depth: int, **kwargs):
        async with self.value_lock:
            price = kwargs["price"]
            update_time = dateutil.parser.parse(kwargs.get("time"))
            recieved_time = kwargs.get("recieved")

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            recieved_lag = now.microsecond - recieved_time
            update_lag = (now - update_time).microseconds

            exporter_manager.add_observation(**{"metric_name": "market_price", "time": kwargs.get("time"), "value": price})

            self.long_buffer.push(price, update_time)
            self.short_buffer.push(price, update_time)
            self.atr_buffer.append(price)

            self.value.price = price
            self.value.long_moving_average = self.long_buffer.get_average(update_time) 
            self.value.short_moving_average = self.short_buffer.get_average(update_time)  
            self.value.average_true_range = self._calc_atr()

            self.metrics_exporter.guage_market_price.set(self.value.price, [self.product], update_time)
            self.metrics_exporter.guage_market_price_long_moving_average.set(self.value.long_moving_average, [self.product], update_time)
            self.metrics_exporter.guage_market_price_short_moving_average.set(self.value.short_moving_average, [self.product], update_time)
            self.metrics_exporter.guage_average_true_range.labels(self.product).set(self.value.average_true_range)
            self.metrics_exporter.guage_price_update_lag.labels(self.product).set(update_lag)
            self.metrics_exporter.guage_price_queue_lag.labels(self.product).set(recieved_lag)
            self.metrics_exporter.guage_price_queue_depth.labels(self.product).set(queue_depth)

            self.events.trigger_event(EventType.PRICE_UPDATE, self.value)


    def _calc_atr(self):
        if len(self.atr_buffer) < 14:
            return 0
        # Calculate ATR using the last 14 prices
        high = max(self.atr_buffer)
        low = min(self.atr_buffer)
        return high - low
