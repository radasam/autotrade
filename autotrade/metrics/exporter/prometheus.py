from prometheus_client import start_http_server, Gauge, Summary, Counter

from autotrade.metrics.exporter.local import MemoryGauge
from autotrade.metrics.exporter.gauge_wrapper import GaugeWrapper

class PrometheusExporter():

    def __init__(self, store_history: bool):
        self.gauge_buy_orders = MemoryGauge("buy_orders", "total value of buy orders at a given point in time", labelnames=["product"], store_history=store_history)
        self.gauge_sell_orders = MemoryGauge("sell_orders", "total value of sell orders at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_order_imbalance = MemoryGauge("order_imbalance", "difference between buy and sell orders", labelnames=["product"], store_history=store_history)
        self.guage_spread = MemoryGauge("spread", "difference between highest buy and lowest sell orders", labelnames=["product"], store_history=store_history)
        self.guage_market_price = GaugeWrapper("market_price", "market price at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_market_price_long_moving_average = GaugeWrapper("market_price_long_moving_average", "moving average of market price at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_market_price_short_moving_average = GaugeWrapper("market_price_short_moving_average", "moving average of market price at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_average_true_range = MemoryGauge("average_true_range", "average true range of market price at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_limit_price = MemoryGauge("limit_price", "limit price at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_order_update_lag = MemoryGauge("order_update_lag", "lag between orders value and true value", labelnames=["product"], store_history=store_history)
        self.guage_order_queue_lag = MemoryGauge("order_queue_lag","time order update spent in the queue", labelnames=["product"], store_history=store_history)
        self.guage_order_queue_depth = MemoryGauge("order_queue_depth", "number of items in the order update queue", labelnames=["product"], store_history=store_history)
        self.guage_price_update_lag = MemoryGauge("price_update_lag", "lag between price value and true value", labelnames=["product"], store_history=store_history)
        self.guage_price_queue_lag = MemoryGauge("price_queue_lag","time price update spent in the queue", labelnames=["product"], store_history=store_history)
        self.guage_price_queue_depth = MemoryGauge("price_queue_depth", "number of items in the price update queue", labelnames=["product"], store_history=store_history)
        self.guage_confidence = MemoryGauge("confidence", "confidence in the current action", labelnames=["product"], store_history=store_history)
        self.guage_cash_balance = MemoryGauge("cash_balance", "cash balance at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_position = MemoryGauge("position", "position at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_average_price = MemoryGauge("average_price", "average price of product at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_pending_position = MemoryGauge("pending_position", "pending position at a given point in time", labelnames=["product"], store_history=store_history)
        self.summary_filled_orders = Summary("filled_orders", "summary of filled orders", labelnames=["product"])
        self.summary_cancelled_orders = Summary("cancelled_orders", "summary of cancelled orders", labelnames=["product"])
        self.guage_take_profit = MemoryGauge("take_profit", "take profit value at a given point in time", labelnames=["product"], store_history=store_history)
        self.take_profit_hit = MemoryGauge("take_profit_hit", "whether take profit was hit at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_stop_losses = MemoryGauge("stop_losses", "stop losses value at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_stop_losses_hit = MemoryGauge("stop_losses_hit", "whether stop losses were hit at a given point in time", labelnames=["product"], store_history=store_history)
        self.guage_action_price = MemoryGauge("action_price", "price at which the action was taken", labelnames=["product"], store_history=store_history)
        self.guage_action_volume = MemoryGauge("action_volume", "volume of the action taken", labelnames=["product"], store_history=store_history)
        self.guage_action_value = MemoryGauge("action_value", "value of the action taken", labelnames=["product"], store_history=store_history)

        self.summary_recieved_messages = Summary("recieved_messages", "summary of websocket messages recieved", labelnames=["product", "channel"])
        pass

    def start(self):
        start_http_server(8000)