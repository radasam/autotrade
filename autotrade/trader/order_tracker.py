from typing import Dict, Tuple

from autotrade.metrics.exporter.prometheus import PrometheusExporter     
from autotrade.types.pending_order import PendingOrder
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL

class OrderTracker():
    def __init__(self, product: str, metrics_exporter: PrometheusExporter):
        self.product = product  
        self.orders: Dict[str, PendingOrder]= {}
        self.metrics_exporter = metrics_exporter

    def add_order(self, pending_order: PendingOrder):
        self.orders[pending_order.client_order_id] = pending_order

        self.update_metrics()

    def remove_order(self, client_order_id):
        if client_order_id in self.orders:
            del self.orders[client_order_id]

        self.update_metrics()    

    def get_order(self, client_order_id):
        return self.orders.get(client_order_id, None)

    def get_all_orders(self):
        return self.orders.values()
    
    def cancel_all_orders(self):
        for order_id in list(self.orders.keys()):
            self.remove_order(order_id)

        self.update_metrics()

    def fill_order(self, client_order_id: str):    
        order = self.get_order(client_order_id)
        if order:
            self.remove_order(client_order_id)

        self.update_metrics()

    def get_pending_position(self) -> Tuple[float, float]:
        pending_position = 0
        for order in self.orders.values():
            if order.side == ORDER_BUY:
                pending_position += order.volume
            else:
                pending_position -= order.volume

        pending_cost = 0
        for order in self.orders.values():
            if order.side == ORDER_BUY:
                pending_cost += order.volume * order.price
            else:
                pending_cost -= order.volume * order.price

        return pending_position, pending_cost
    
    def update_metrics(self):
        pending_position, pending_cost = self.get_pending_position()
        self.metrics_exporter.guage_pending_position.labels(self.product).set(pending_position) 