import json
import logging
import datetime

from autotrade.settings.secrets import get_secret_key, get_api_key
from autotrade.metrics.metrics import Metrics
from autotrade.events.events import Events
from autotrade.types.order_update import OrderUpdate

from coinbase.websocket import WSClient

class MarketSocket(): 
    def __init__(self, product: str, metrics: Metrics, events: Events):
        api_key = get_api_key() 
        api_secret = get_secret_key()
        self.product = product
        self.metrics = metrics
        self.events = events
        self.client = WSClient(api_key=api_key, api_secret=api_secret, on_message=self.on_message, verbose=True)

    def on_message(self, message: str):
        jsonmsg = json.loads(message)
        update_count = 0
        # logging.info("got msg")
        recieved = datetime.datetime.now().microsecond
        if "channel" not in jsonmsg:
            print(jsonmsg)
            return

        channel = jsonmsg["channel"]
        if channel == "l2_data":
            order_updates = []
            events = jsonmsg["events"]     
            for event in events:
                event_type = event["type"]
                if event_type == "snapshot":
                    logging.info("recieved snapshot")
                product = event["product_id"]
                updates = event["updates"]
                for update in updates:
                    update_count += 1
                    order_updates.append(OrderUpdate(side=update["side"], price=float(update["price_level"]), volume=float(update["new_quantity"])))
            self.metrics.update_order(product, order_updates, update["event_time"], recieved)
            self.metrics.update_recieved_messages(product, channel, 1)
        if channel == "ticker":
            events = jsonmsg["events"]
            for event in events:
                tickers = event["tickers"]
                for ticker in tickers:
                    update_count += 1
                    product = ticker["product_id"]
                    price = float(ticker["price"])
                    timestamp = jsonmsg["timestamp"]
                    self.metrics.update_market_price(product, price, timestamp, recieved)
            self.metrics.update_recieved_messages(product, channel, update_count)


    def start(self):
        self.client.open()
        self.client.subscribe([self.product], ["heartbeats" , "level2", "ticker"])
        self.client.run_forever_with_exception_check()
        self.client.close()
