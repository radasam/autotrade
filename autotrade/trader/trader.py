import logging

from autotrade.broker.broker import Broker
from autotrade.metrics.metrics import Metrics
from autotrade.types.order_metrics import OrderMetrics, PriceMetrics
from autotrade.settings.config import ConfigGetter
from autotrade.types.broker_error import EXISTING_ORDER_ERROR, INSUFFICIENT_FUNDS_ERROR, INSUFFICIENT_PRODUCT_ERROR
from autotrade.trader.position_tracker import PositionTracker
from autotrade.trader.order_tracker import OrderTracker
from autotrade.types.pending_order import PendingOrder
from autotrade.trader.strategies.strategy_mux import StrategyMux
from autotrade.trader.strategies.order_imbalance import OrderImbalanceStrategy
from autotrade.trader.strategies.moving_average import MovingAverageStrategy
class Trader:
    def __init__(self, product: str, broker: Broker, metrics: Metrics, config_getter: ConfigGetter):
        self.product = product
        self.broker = broker
        self.metrics = metrics
        self.config_getter = config_getter
        self.order_tracker = OrderTracker(product, metrics.metrics_exporter)
        self.PositionTracker = PositionTracker(self.product, 1000, 0.01, self.order_tracker, config_getter, metrics.metrics_exporter)
        self.strategy_mux = StrategyMux(config_getter)
        
        self.strategy_mux.register_strategy(OrderImbalanceStrategy(), "order_imbalance")
        self.strategy_mux.register_strategy(MovingAverageStrategy(), "moving_average")
        

    async def handle_price_update(self, price_metrics: PriceMetrics):
        order_metrics = await self.metrics.get_order_metrics()
        await self.handle_update(order_metrics, price_metrics)

    async def handle_order_update(self, order_metrics: OrderMetrics):
        price_metrics = await self.metrics.get_price_metrics()
        await self.handle_update(order_metrics, price_metrics)

    async def handle_order_filled(self, pending_order: dict):
        order = PendingOrder(**pending_order)
        self.PositionTracker.handle_order_filled(order)
        self.order_tracker.fill_order(order.client_order_id)
        print("order filled done")

    async def handle_order_cancelled(self, pending_order: dict):
        order = PendingOrder(**pending_order)
        if order.filled_size > 0:
            self.PositionTracker.handle_order_filled(order)
        self.order_tracker.remove_order(order.client_order_id)


    async def check_action(self, order_metrics: OrderMetrics, price_metrics: PriceMetrics):
        should_take_profit = False
        should_stop_losses = False
        if price_metrics.price ==0:
            return

        action, confidence, limit_price = await self.strategy_mux.get_signals(order_metrics, price_metrics)

        if action != 0:
            return action, confidence, limit_price

        
        should_take_profit, limit_price = await self.PositionTracker.check_take_profit(confidence, order_metrics.spread, price_metrics.price)

        if should_take_profit:
            logging.info(f"Action: {action}, Confidence: {confidence}, Limit Price: {limit_price}, Take Profit: {should_take_profit}")
            return 1, 1, limit_price

        should_stop_losses, limit_price = await self.PositionTracker.check_stop_losses(price_metrics.price, price_metrics.long_moving_average)

        if should_stop_losses:
            logging.info(f"Action: {action}, Confidence: {confidence}, Limit Price: {limit_price}, Stop Loss: {should_stop_losses}")
            return -1, 1, limit_price
        
        return 0, 0, 0

    async def handle_update(self, order_metrics: OrderMetrics, price_metrics: PriceMetrics):

        if self.order_tracker.get_pending_position()[0] != 0:
            return

        action, confidence, limit_price = await self.check_action(order_metrics, price_metrics)

        if action == 0:
            return

        position_delta, cancel_pending = self.PositionTracker.get_position_delta(limit_price ,action, confidence)
        if cancel_pending:
            self.broker.cancel_current_order()
            return 

        if position_delta == 0:
            return
            
        self.metrics.metrics_exporter.guage_limit_price.labels(self.product).set(limit_price)

        pending_order, err = await self.broker.create_limit_order(str(position_delta), str(limit_price), confidence, 10)
        if err:
            if err.type == EXISTING_ORDER_ERROR:
                logging.info(f"Existing order error: {err}")
                return
            if err.type == INSUFFICIENT_FUNDS_ERROR or err.type == INSUFFICIENT_PRODUCT_ERROR:
                logging.error(f"Insufficient funds or product error: {err}")
                self.broker.cancel_current_order()
                return
            logging.error(f"Error creating order: {err}")
            logging.info(f"{self.PositionTracker.position}")
            return
        if pending_order:
            self.order_tracker.add_order(pending_order)

        return
        


