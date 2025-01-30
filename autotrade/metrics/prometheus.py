from prometheus_client import start_http_server, Gauge, Summary

class PrometheusExporter():

    def __init__(self):
        self.gauge_buy_orders = Gauge("buy_orders", "total value of buy orders at a given point in time", labelnames=["product"])
        self.gauge_sell_orders = Gauge("sell_orders", "total value of sell orders at a given point in time", labelnames=["product"])
        self.guage_market_price = Gauge("market_price", "market price at a given point in time", labelnames=["product"])
        self.guage_order_update_lag = Gauge("order_update_lag", "lag between orders value and true value", labelnames=["product"])
        self.guage_order_queue_lag = Gauge("order_queue_lag","time order update spent in the queue", labelnames=["product"])
        self.guage_order_queue_depth = Gauge("order_queue_depth", "number of items in the order update queue", labelnames=["product"])
        self.guage_price_update_lag = Gauge("price_update_lag", "lag between price value and true value", labelnames=["product"])
        self.guage_price_queue_lag = Gauge("price_queue_lag","time price update spent in the queue", labelnames=["product"])
        self.guage_price_queue_depth = Gauge("price_queue_depth", "number of items in the price update queue", labelnames=["product"])

        self.summary_recieved_messages = Summary("recieved_messages", "summary of websocket messages recieved", labelnames=["product", "channel"])
        pass

    def start(self):
        start_http_server(8000)