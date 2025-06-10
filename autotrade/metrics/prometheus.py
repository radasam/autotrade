from prometheus_client import start_http_server, Gauge, Summary

class PrometheusExporter():

    def __init__(self):
        self.gauge_buy_orders = Gauge("buy_orders", "total value of buy orders at a given point in time", labelnames=["product"])
        self.gauge_sell_orders = Gauge("sell_orders", "total value of sell orders at a given point in time", labelnames=["product"])
        self.guage_order_imbalance = Gauge("order_imbalance", "difference between buy and sell orders", labelnames=["product"])
        self.guage_spread = Gauge("spread", "difference between highest buy and lowest sell orders", labelnames=["product"])
        self.guage_market_price = Gauge("market_price", "market price at a given point in time", labelnames=["product"])
        self.guage_market_price_long_moving_average = Gauge("market_price_long_moving_average", "moving average of market price at a given point in time", labelnames=["product"])
        self.guage_market_price_short_moving_average = Gauge("market_price_short_moving_average", "moving average of market price at a given point in time", labelnames=["product"])
        self.guage_average_true_range = Gauge("average_true_range", "average true range of market price at a given point in time", labelnames=["product"])
        self.guage_limit_price = Gauge("limit_price", "limit price at a given point in time", labelnames=["product"])
        self.guage_order_update_lag = Gauge("order_update_lag", "lag between orders value and true value", labelnames=["product"])
        self.guage_order_queue_lag = Gauge("order_queue_lag","time order update spent in the queue", labelnames=["product"])
        self.guage_order_queue_depth = Gauge("order_queue_depth", "number of items in the order update queue", labelnames=["product"])
        self.guage_price_update_lag = Gauge("price_update_lag", "lag between price value and true value", labelnames=["product"])
        self.guage_price_queue_lag = Gauge("price_queue_lag","time price update spent in the queue", labelnames=["product"])
        self.guage_price_queue_depth = Gauge("price_queue_depth", "number of items in the price update queue", labelnames=["product"])
        self.guage_confidence = Gauge("confidence", "confidence in the current action", labelnames=["product"])
        self.guage_cash_balance = Gauge("cash_balance", "cash balance at a given point in time", labelnames=["product"])
        self.guage_position = Gauge("position", "position at a given point in time", labelnames=["product"])
        self.guage_position_cost = Gauge("position_cost", "position cost at a given point in time", labelnames=["product"])
        self.guage_average_price = Gauge("average_price", "average price of product at a given point in time", labelnames=["product"])
        self.guage_pending_position = Gauge("pending_position", "pending position at a given point in time", labelnames=["product"])
        self.guage_pending_cash= Gauge("pending_cash", "pending value at a given point in time", labelnames=["product"])
        self.summary_filled_orders = Summary("filled_orders", "summary of filled orders", labelnames=["product"])
        self.summary_cancelled_orders = Summary("cancelled_orders", "summary of cancelled orders", labelnames=["product"])
        self.guage_take_profit = Gauge("take_profit", "take profit value at a given point in time", labelnames=["product"])
        self.take_profit_hit = Gauge("take_profit_hit", "whether take profit was hit at a given point in time", labelnames=["product"])
        self.guage_stop_losses = Gauge("stop_losses", "stop losses value at a given point in time", labelnames=["product"])
        self.guage_stop_losses_hit = Gauge("stop_losses_hit", "whether stop losses were hit at a given point in time", labelnames=["product"])
        self.guage_profig = Gauge("profit", "profit at a given point in time", labelnames=["product"])

        self.summary_recieved_messages = Summary("recieved_messages", "summary of websocket messages recieved", labelnames=["product", "channel"])
        pass

    def start(self):
        start_http_server(8000)