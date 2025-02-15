import threading
import asyncio

from autotrade.markets.market_socket import MarketSocket
from autotrade.metrics.metrics import Metrics
from autotrade.events.events import Events
from autotrade.exporter.exporter import Exporter
from autotrade.exporter.connectors.s3_connector import S3Connector
from autotrade.exporter.exporter_manager import exporter_manager
from autotrade.settings.config import config
from autotrade.settings.contants import get_export_bucket

class Engine():

    def __init__(self, product: str):
        self.loop = asyncio.get_event_loop()
        self.product = product
        self.event_handler = Events()
        self.metrics = Metrics(self.event_handler)
        self.markets_socket = MarketSocket(product, self.metrics, self.event_handler)
        self.event_handler.add_handler("check_action", "orders_updated", self.on_orders_update)

    def setup(self):
        export_bucket = get_export_bucket()
        exporter_manager.add_exporter("order_buys", Exporter("order_buys", 1000, S3Connector(export_bucket, True)))
        exporter_manager.add_exporter("order_sells", Exporter("order_sells", 1000, S3Connector(export_bucket, True)))
        exporter_manager.add_exporter("market_price", Exporter("market_price", 1000, S3Connector(export_bucket, True)))
        pass

    def start(self):
        exporter_manager.start()
        self.event_handler.start()
        self.metrics.start_metrics_exporter()
        self.metrics.add_product(self.product)
        config.start()
        self.markets_socket.start()


    def on_orders_update(self):
        print("orders_updated")