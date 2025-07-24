from autotrade.trader.order_tracker import OrderTracker
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL
from autotrade.types.pending_order import PendingOrder
from autotrade.metrics.exporter.prometheus import PrometheusExporter

pe = PrometheusExporter()

def test_order_tracker_add_order():
    ot = OrderTracker("BTC-USD", pe)
    order = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order)
    assert ot.get_order("1234") == order
    assert ot.get_pending_position() == (0.01, 100)

def test_order_tracker_remove_order():
    ot = OrderTracker("BTC-USD", pe)
    order = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order)
    ot.remove_order("1234")
    
    assert ot.get_order("1234") is None
    assert ot.get_pending_position() == (0, 0)

def test_order_tracker_fill_order():
    ot = OrderTracker("BTC-USD", pe)
    order = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order)
    ot.fill_order("1234")
    
    assert ot.get_order("1234") is None
    assert ot.get_pending_position() == (0, 0)

def test_order_tracker_get_all_orders():
    ot = OrderTracker("BTC-USD", pe)
    order1 = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    order2 = PendingOrder(side=ORDER_BUY, volume=0.02, price=20000, client_order_id="5678", order_id="5678", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order1)
    ot.add_order(order2)
    
    orders = ot.get_all_orders()

    assert len(orders) == 2

    assert ot.get_pending_position() == (0.03, 500)  # Only order1 contributes to pending position

    assert order1 in orders
    assert order2 in orders

def test_order_tracker_cancel_all_orders():
    ot = OrderTracker("BTC-USD", pe)
    order1 = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    order2 = PendingOrder(side=ORDER_BUY, volume=0.02, price=20000, client_order_id="5678", order_id="5678", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order1)
    ot.add_order(order2)
    
    ot.cancel_all_orders()
    
    assert len(ot.get_all_orders()) == 0
    assert ot.get_pending_position() == (0, 0)

def test_order_tracker_mixed_orders():
    ot = OrderTracker("BTC-USD", pe)
    order1 = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    order2 = PendingOrder(side=ORDER_SELL, volume=0.02, price=20000, client_order_id="5678", order_id="5678", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order1)
    ot.add_order(order2)
    
    assert len(ot.get_all_orders()) == 2
    assert ot.get_pending_position() == (-0.01, -300)  # Only order1 contributes to pending position


def test_order_tracker_cancel_correct_order():
    ot = OrderTracker("BTC-USD", pe)
    order1 = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    order2 = PendingOrder(side=ORDER_BUY, volume=0.02, price=20000, client_order_id="5678", order_id="5678", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    
    ot.add_order(order1)
    ot.add_order(order2)
    
    ot.remove_order("1234")
    
    assert ot.get_order("1234") is None
    assert len(ot.get_all_orders()) == 1
    assert ot.get_order("5678") == order2