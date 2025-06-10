import pytest

from autotrade.trader.order_tracker import OrderTracker
from autotrade.trader.position_tracker import PositionTracker
from autotrade.metrics.prometheus import PrometheusExporter
from autotrade.types.pending_order import PendingOrder
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL

pe = PrometheusExporter()

def test_position_tracker_update_pending(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    ot.add_order(PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z"))

    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1000

def test_position_tracker_fill_order(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=10000)
    ot.add_order(po)

    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1000
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0.01
    assert pt.position_cost == 100
    assert pt.avg_price == 10000
    assert pt.cash == 900

def test_position_tracker_fill_order_partial(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.005, avg_filled_price=10000)
    ot.add_order(po)

    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1000
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0.005
    assert pt.position_cost == 50
    assert pt.avg_price == 10000
    assert pt.cash == 950

def test_position_tracker_fill_order_sell(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    pt.position = 0.01
    pt.position_cost = 100
    pt.avg_price = 10000
    po = PendingOrder(side=ORDER_SELL, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=10000)
    ot.add_order(po)

    assert pt.position == 0.01
    assert pt.position_cost == 100
    assert pt.avg_price == 10000
    assert pt.cash == 1000
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1100

def test_position_tracker_get_position_delta(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    position_delta, should_cancel = pt.get_position_delta(10000, 1, 0.5)

    assert position_delta == 0.05
    assert should_cancel == False

def test_position_tracker_get_position_delta_sell_existing_position(with_config):
    # if we have an existing position, we should not sell because of low confidence
    # instead sells will be initiated by take profit
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    pt.position = 1
    position_delta, should_cancel = pt.get_position_delta(10000, -1, 0.5)

    assert position_delta == 0
    assert should_cancel == False

def test_position_tracker_get_position_delta_with_pending(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    ot.add_order(po)
    position_delta, should_cancel = pt.get_position_delta(10000, 1, 0.5)

    assert position_delta == 0.04
    assert should_cancel == False

def test_position_tracker_get_position_delta_buy_to_sell(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    ot.add_order(po)
    position_delta, should_cancel = pt.get_position_delta(10000, -1, 0.5)

    assert position_delta == 0
    assert should_cancel == True

def test_position_tracker_get_position_delta_sell_to_buy(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_SELL, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z")
    ot.add_order(po)
    position_delta, should_cancel = pt.get_position_delta(10000, 1, 0.5)

    assert position_delta == 0
    assert should_cancel == True

def test_position_tracker_fill_order_two_buy(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=10000)
    ot.add_order(po)

    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1000
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0.01
    assert pt.position_cost == 100
    assert pt.avg_price == 10000
    assert pt.cash == 900

    po2 = PendingOrder(side=ORDER_BUY, volume=0.01, price=20000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=20000)
    ot.add_order(po2)
    
    pt.handle_order_filled(po2)
    ot.fill_order("1234")

    assert pt.position == 0.02
    assert pt.position_cost == 300
    assert pt.avg_price == 15000
    assert pt.cash == 700

def test_position_tracker_fill_order_buy_sell(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    po = PendingOrder(side=ORDER_BUY, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=10000)
    ot.add_order(po)

    assert pt.position == 0
    assert pt.position_cost == 0
    assert pt.avg_price == 0
    assert pt.cash == 1000
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0.01
    assert pt.position_cost == 100
    assert pt.avg_price == 10000
    assert pt.cash == 900

    po2 = PendingOrder(side=ORDER_SELL, volume=0.005, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.005, avg_filled_price=10000)
    ot.add_order(po2)
    
    pt.handle_order_filled(po2)
    ot.fill_order("1234")

    assert pt.position == 0.005
    assert pt.position_cost == 50
    assert pt.avg_price == 10000
    assert pt.cash == 950

def test_position_tracker_fill_order_two_sell(with_config):
    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    pt.position = 0.02
    pt.position_cost = 200
    pt.avg_price = 10000
    po = PendingOrder(side=ORDER_SELL, volume=0.01, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.01, avg_filled_price=10000)
    ot.add_order(po)
    
    pt.handle_order_filled(po)
    ot.fill_order("1234")
    
    assert pt.position == 0.01
    assert pt.position_cost == 100
    assert pt.avg_price == 10000
    assert pt.cash == 1100

    po2 = PendingOrder(side=ORDER_SELL, volume=0.005, price=10000, client_order_id="1234", order_id="1234", status="OPEN", timeout_at="2023-10-01T00:00:00Z", filled_size=0.005, avg_filled_price=10000)
    ot.add_order(po2)
    
    pt.handle_order_filled(po2)
    ot.fill_order("1234")

    assert pt.position == 0.005
    assert pt.position_cost == 50
    assert pt.avg_price == 10000
    assert pt.cash == 1150

@pytest.mark.asyncio
async def test_position_tracker_calulate_take_profit(with_config):
    with_config.set_value("take_profit_multiplier", 100)  # 10% profit

    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    pt.position = 0.01
    pt.position_cost = 100
    pt.avg_price = 10000
    pt.entry_confidence = 1

    spread = 1  # 1% spread

    take_profit_price = await pt._calculate_take_profit(10000, "buy", spread, 0.8)  # 10% profit
    assert take_profit_price == 10060

@pytest.mark.asyncio
async def test_position_tracker_check_stop_losses(with_config):
    with_config.set_value("stop_loss_percentage", 0.05)  # 5% stop loss
    with_config.set_value("stop_loss_offset", 0.05)  # 1% offset

    ot = OrderTracker("BTC-USD", pe)
    pt = PositionTracker("BTC-USD", 1000, 0.01, ot, with_config, pe)
    pt.position = 0.01
    pt.position_cost = 100
    pt.avg_price = 10000
    pt.entry_confidence = 1

    stop_losses, volume, price =  await pt.check_stop_losses(940, 1000)

    assert stop_losses == True
    assert volume == -0.01
    assert price == 940 * 0.95  # 5% stop loss