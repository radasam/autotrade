import math
import logging
from typing import Tuple

from autotrade.metrics.prometheus import PrometheusExporter     
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL   
from autotrade.trader.order_tracker import OrderTracker
from autotrade.types.pending_order import PendingOrder
from autotrade.settings.config import ConfigGetter

class PositionTracker:
    def __init__(self, product: str, cash: float, tick_size: float, order_tracker: OrderTracker, config_getter: ConfigGetter, metrics_exporter: PrometheusExporter):
        self.product = product
        self.tick_size = tick_size
        self.metrics_exporter = metrics_exporter
        self.config_getter = config_getter
        self.cash = cash
        self.position_value = 0
        self.position_cost = 0
        self.position = 0
        self.avg_price = 0
        self.order_tracker = order_tracker
        self.entry_confidence = 0
        self.take_profit = -1
        pass

    async def _calculate_take_profit(
        self, 
        entry_price: float, 
        side: str,
        spread: float,
        confidence: float
    ):
        """Calculate dynamic take profit level based on entry, spread, and confidence"""
        config = await self.config_getter.get_config()
        
        # Scale the take profit by confidence level
        tp_multiplier = config.take_profit_multiplier * (1 - (abs(confidence) * config.take_profit_sensitivity))

        if side == 'buy':
            return entry_price + (spread * tp_multiplier)
        else:  # sell
            return entry_price - (spread * tp_multiplier)
    
    async def update_take_profit(self, current_confidence, current_spread):
        """Update take profit and stop loss based on changing market conditions"""
        if self.position <= 0:
            self.take_profit = -1
            return

        # Only update targets if confidence has changed significantly
        confidence_change = abs(current_confidence - self.entry_confidence)
        
        if round(confidence_change,5) >= 0.2:  # Threshold for significant confidence change
            # Recalculate take profit with current data
            self.take_profit = await self._calculate_take_profit(
                self.avg_price, 
                'buy' if self.position > 0 else 'sell',
                current_spread, 
                current_confidence
            )

    async def check_take_profit(self, current_confidence: float, current_spread: float, price: float) -> Tuple[bool, float]:
        if current_confidence == 0:
            return False, 0

        await self.update_take_profit(current_confidence, current_spread)
        
        if self.take_profit == -1:
            return False, 0
        
        self.metrics_exporter.guage_take_profit.labels(self.product).set(self.take_profit)

        """Check if the current price has hit the take profit level"""
        if self.position > 0 and price >= self.take_profit:
            self.metrics_exporter.take_profit_hit.labels(self.product).set(1)
            return True, self.take_profit
        elif self.position < 0 and price <= self.take_profit:
            self.metrics_exporter.take_profit_hit.labels(self.product).set(1)
            return True, self.take_profit
        
        return False, 0
    
    async def check_stop_losses(self, price: float, moving_average_price: float) -> Tuple[bool, float]:
        """Check if the current price has hit the stop loss level"""
        config = await self.config_getter.get_config()

        stop_losses = moving_average_price * (1 - config.stop_loss_percentage)

        self.metrics_exporter.guage_stop_losses.labels(self.product).set(stop_losses)
        
        if self.position > 0 and price <= stop_losses:
            self.metrics_exporter.guage_stop_losses_hit.labels(self.product).set(1)
            return True, price * (1 - config.stop_less_offset)
        
        return False, 0  
        
    def calculate_target_position(self, price: float, action: int, confidence: float) -> float:
        # for now lets not short and just close out our long if we have one
        if action <0 and self.position < 0:
            return 0

        if action < 0 and self.position >= 0:
            return 0

        
        max_position = (self.cash) / price
        target_position = max_position * confidence * action

        return target_position

    def get_position_delta(self, price: float, action: int, confidence: float)-> Tuple[float, bool]:

        pending_position, _ = self.order_tracker.get_pending_position()

        # if we have a pending position on the opposite side, we need to close it out first
        # the order will be cancelled
        if (pending_position > 0) and action < 0:
            return 0, True
            
        
        # if we have a pending position on the same side, we need to close it out first
        if (pending_position < 0) and action > 0:
            return 0, True
        
        if (self.position > 0 and action < 0) or (self.position < 0 and action > 0):
            # if we have a position on the opposite side, we should let take profit handle it
            return 0, False


        target_position = self.calculate_target_position(price, action, confidence)
        raw_position_delta = target_position  - self.position - pending_position
        raw_volume_delta = raw_position_delta * price

        
        adj_position_delta = math.floor(raw_position_delta/0.00000001)*0.00000001
        adj_volume_delta = round(adj_position_delta * price, 2)

        if (abs(adj_position_delta) * price) < self.tick_size:
            return 0, False
        
        return adj_position_delta, False


    def handle_order_filled(self, order: PendingOrder):
        volume = order.filled_size
        price = order.avg_filled_price
        side = order.side
        cost = volume * price
        self.cash -= cost if side == ORDER_BUY else -cost
        self.position += volume if side == ORDER_BUY else -volume
        self.position_cost += cost if side == ORDER_BUY else -cost
        self.position_value = self.position * price

        if side == ORDER_BUY:
            self.entry_confidence = order.confidence
        if side == ORDER_SELL:
            self.entry_confidence = 0

        self.new_take_profit = -1
        
        print(f"order filled: {order}, cash: {self.cash}, position: {self.position}, position_cost: {self.position_cost}, position_value: {self.position_value}")

        profit = (price - self.avg_price) * volume

        if self.position > 0:
            self.avg_price = self.position_cost / self.position
        else:
            self.avg_price = 0
            self.position_value = 0
            self.position_cost = 0

        self.metrics_exporter.guage_cash_balance.labels(self.product).set(self.cash)
        self.metrics_exporter.guage_position.labels(self.product).set(self.position)
        self.metrics_exporter.guage_position_cost.labels(self.product).set(self.position_cost)
        self.metrics_exporter.guage_average_price.labels(self.product).set(self.avg_price)
        self.metrics_exporter.guage_profit(labels=self.product).set(profit if self.position > 0 else 0)


    def get_position(self):
        return self.position
    
