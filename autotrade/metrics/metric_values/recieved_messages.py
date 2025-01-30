from autotrade.metrics.metric_values.main import MetricValue
from autotrade.metrics.prometheus import PrometheusExporter

class Recieved_Messages(MetricValue):
    def __init__(self, product: str, metrics_exporter: PrometheusExporter):
        super().__init__()
        self.product = product
        self.metrics_exporter = metrics_exporter
        self.market_price = 0

    def get_value(self):
        return self.market_price
    
    async def update(self, queue_depth: int, **kwargs):
        channel = kwargs["channel"]
        update_count = kwargs["update_count"]

        self.metrics_exporter.summary_recieved_messages.labels(self.product, channel).observe(update_count)