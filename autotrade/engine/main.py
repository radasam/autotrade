import logging
import asyncio
from  datetime import datetime, timezone, timedelta
import json

from autotrade.providers.backtesting_provider import BacktestingProvider
from autotrade.providers.coinbase_provider import CoinbaseProvider
from autotrade.metrics.metrics import MetricsManager
from autotrade.events.events import Events
from autotrade.exporter.exporter import Exporter
from autotrade.exporter.connectors.localfile_connector import LocalFileConnector
from autotrade.exporter.exporter_manager import exporter_manager
from autotrade.settings.config import config
from autotrade.settings.contants import get_export_bucket
from autotrade.trader.trader import Trader
from autotrade.broker.paper_broker import PaperBroker
from autotrade.events.event_types import EventType

class Engine():

    def __init__(self, product: str):
        self.loop = asyncio.get_event_loop()
        self.product = product
        self.event_handler = Events()
        self.metrics = MetricsManager(product, self.event_handler)
        self.provider = CoinbaseProvider(product, self.on_message)
        # self.provider = BacktestingProvider(start_time=datetime(2025, 5,25, 15, 00, 00, tzinfo=timezone.utc), end_time=datetime(2025, 12, 11, 15, 00, 00, tzinfo=timezone.utc), interval=timedelta(seconds=0.5), real_time_factor=10.0, folder_path="./exported_data",  on_message=self.on_message)
        self.broker = PaperBroker(product,1000, self.event_handler)
        self.trader = Trader(product, self.broker, self.metrics.metrics, config)

    def setup(self):
        exporter_manager.add_exporter("orders", Exporter("orders", 40000, timedelta(hours=1), LocalFileConnector("/Users/samradage/repos/autotrade/exported_data")))
        exporter_manager.add_exporter("market_price", Exporter("market_price", 20000, timedelta(hours=1), LocalFileConnector("/Users/samradage/repos/autotrade/exported_data")))

        self.event_handler.add_handler("handle_price_update", EventType.PRICE_UPDATE, self.broker.update_price)
        self.event_handler.add_handler("handle_price_update", EventType.PRICE_UPDATE, self.trader.handle_price_update)
        self.event_handler.add_handler("handle_order_update", EventType.ORDER_UPDATE, self.trader.handle_order_update)
        self.event_handler.add_handler("handle_order_book_update", EventType.ORDER_BOOK_UPDATE, self.broker.update_order_book)
        self.event_handler.add_handler("handle_filled_order", EventType.ORDER_FILLED, self.trader.handle_order_filled)
        self.event_handler.add_handler("handle_canceled_order", EventType.ORDER_CANCELLED, self.trader.handle_order_cancelled)
        pass

    def on_message(self, message: str):
        is_snapshot = False
        jsonmsg = json.loads(message)
        update_count = 0
        recieved = datetime.now().microsecond
        if "channel" not in jsonmsg:
            print(jsonmsg)
            return

        channel = jsonmsg["channel"]
        if channel == "l2_data":
            events = jsonmsg["events"]     
            for event in events:
                event_type = event["type"]
                if event_type == "snapshot":
                    is_snapshot = True
                    logging.debug("snapshot")
                updates = event["updates"]
                self.metrics.update_order(updates, jsonmsg["timestamp"], recieved)
            self.metrics.update_recieved_messages(channel, 1)
        elif channel == "ticker":
            events = jsonmsg["events"]
            for event in events:
                tickers = event["tickers"]
                for ticker in tickers:
                    update_count += 1
                    price = float(ticker["price"])
                    timestamp = jsonmsg["timestamp"]
                    self.metrics.update_market_price(price, timestamp, recieved)
            self.metrics.update_recieved_messages(channel, update_count)
        elif channel == "heartbeats":
            pass
        else:
            logging.error(f"unknown channel {channel}") 

        if is_snapshot:
            logging.debug("snapshot done")

    async def start(self):
        self.metrics.start_metrics_exporter()
        await asyncio.gather(self.metrics.start(), self.provider.start(), exporter_manager.start(), self.event_handler.start(), self.broker.start(), config.start())
