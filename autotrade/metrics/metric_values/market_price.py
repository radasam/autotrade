import dateutil.parser
import datetime

from autotrade.metrics.metric_values.main import MetricValue
from autotrade.metrics.prometheus import PrometheusExporter

class MarketPrice(MetricValue):
    def __init__(self, product: str, metrics_exporter: PrometheusExporter):
        super().__init__()
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.market_price = 0

    def get_value(self):
        return self.market_price
    
    async def update(self, queue_depth: int, **kwargs):
        price = kwargs["price"]
        update_time = dateutil.parser.parse(kwargs.get("time"))
        recieved_time = kwargs.get("recieved")

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        recieved_lag = now.microsecond - recieved_time
        update_lag = (now - update_time).microseconds

        self.market_price = price
        self.metrics_exporter.guage_market_price.labels(self.product).set(price)
        self.metrics_exporter.guage_price_update_lag.labels(self.product).set(update_lag)
        self.metrics_exporter.guage_price_queue_lag.labels(self.product).set(recieved_lag)
        self.metrics_exporter.guage_price_queue_depth.labels(self.product).set(queue_depth)