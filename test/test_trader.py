import asyncio
import pytest
from datetime import datetime

from autotrade.broker.paper_broker import PaperBroker
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL
from autotrade.metrics.metrics import Metrics
from autotrade.metrics.prometheus import PrometheusExporter
from autotrade.trader.trader import Trader
from autotrade.types.order_metrics import OrderMetrics
from autotrade.types.pending_order import PendingOrder
from test.mocks.events import MockEvents

pe = PrometheusExporter()

@pytest.mark.asyncio
async def test_trader_calculate_signals_buy(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=1400,
        sell_volume=600,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=0.4
    )

    action, confidence, price_offset = await t.calculate_signals(order_metrics, 100)
    assert action == 1
    assert confidence == 0.8
    assert price_offset == 16


@pytest.mark.asyncio
async def test_trader_calculate_signals_sell(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=600,
        sell_volume=1400,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=-0.4
    )

    action, confidence, price_offset = await t.calculate_signals(order_metrics, 100)
    assert action == -1
    assert confidence == 0.8
    assert price_offset == -16

@pytest.mark.asyncio
async def test_trader_calculate_signals_no_signal(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=600,
        sell_volume=600,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=0.1
    )

    action, confidence, price_offset = await t.calculate_signals(order_metrics, 100)
    assert action == 0
    assert confidence == 0
    assert price_offset == 0

@pytest.mark.asyncio
async def test_trader_calculate_signals_higher_confidence_buy(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=1500,
        sell_volume=500,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=0.5
    )

    action, confidence, price_offset = await t.calculate_signals(order_metrics, 100)
    assert action == 1
    assert confidence == 1
    assert price_offset == 20

@pytest.mark.asyncio
async def test_trader_calculate_signals_higher_confidence_sell(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=500,
        sell_volume=1500,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=-0.5
    )

    action, confidence, price_offset = await t.calculate_signals(order_metrics, 100)
    assert action == -1
    assert confidence == 1
    assert price_offset == -20

@pytest.mark.asyncio
async def test_trader_handle_order_filled(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    pendingOrder = PendingOrder(
        side=ORDER_BUY,
        order_id="123",
        client_order_id="123",
        filled_size=1,
        avg_filled_price=100,
        status="OPEN",
        product=product,
        volume=1,
        price=100,
        timeout_at=datetime.now()
    )

    t.order_tracker.add_order(pendingOrder)

    await t.handle_order_filled(pendingOrder.model_dump())

    assert t.PositionTracker.position == 1
    assert t.PositionTracker.position_cost == 100
    assert t.PositionTracker.cash == 900
    assert t.order_tracker.get_pending_position() == (0, 0)

@pytest.mark.asyncio
async def test_trader_handle_order_cancelled(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    pendingOrder = PendingOrder(
        side=ORDER_BUY,
        order_id="123",
        client_order_id="123",
        filled_size=0,
        avg_filled_price=0,
        status="OPEN",
        product=product,
        volume=1,
        price=100,
        timeout_at=datetime.now()
    )

    t.order_tracker.add_order(pendingOrder)

    await t.handle_order_cancelled(pendingOrder.model_dump())

    assert t.PositionTracker.position == 0
    assert t.PositionTracker.position_cost == 0
    assert t.PositionTracker.cash == 1000
    assert t.order_tracker.get_pending_position() == (0, 0)

@pytest.mark.asyncio
async def test_trader_handle_order_cancelled_partially_filled(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    pendingOrder = PendingOrder(
        side=ORDER_BUY,
        order_id="123",
        client_order_id="123",
        filled_size=0.5,
        avg_filled_price=100,
        status="OPEN",
        product=product,
        volume=1,
        price=100,
        timeout_at=datetime.now()
    )

    t.order_tracker.add_order(pendingOrder)

    await t.handle_order_cancelled(pendingOrder.model_dump())

    assert t.PositionTracker.position == 0.5
    assert t.PositionTracker.position_cost == 50
    assert t.PositionTracker.cash == 950
    assert t.order_tracker.get_pending_position() == (0, 0)

@pytest.mark.asyncio
async def test_trader_buy_order_into_sell_order(with_config):
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)

    pendingOrder = PendingOrder(
        side=ORDER_BUY,
        order_id="123",
        client_order_id="123",
        filled_size=1,
        avg_filled_price=100,
        status="OPEN",
        product=product,
        volume=1,
        price=100,
        timeout_at=datetime.now()
    )

    t.order_tracker.add_order(pendingOrder)
    pb.active_order = pendingOrder
    pb.active_order.status = "FILLED"

    await pb.check_current_order()

    assert pb.active_order == None
    await t.handle_order_filled(pendingOrder.model_dump())

    assert t.PositionTracker.position == 1
    assert t.PositionTracker.position_cost == 100
    assert t.PositionTracker.cash == 900
    assert t.order_tracker.get_pending_position() == (0, 0)

    with_config.set_value("spread_threshold", 0.04)
    with_config.set_value("imbalance_threshold", 0.3)
    with_config.set_value("min_signals_for_buy_action", 1)
    with_config.set_value("min_signals_for_sell_action", 1)

    order_metrics = OrderMetrics(
        buy_volume=600,
        sell_volume=1400,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=4,
        imbalance=-0.4
    )

    await t.check_action(order_metrics, 100)
    assert pb.active_order is None


@pytest.mark.asyncio
async def test_trader_hit_take_profit(with_config):
    with_config.set_value("take_profit_multiplier", 100)  # 10% profit
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)
    t.PositionTracker.position = 0.01
    t.PositionTracker.position_cost = 100
    t.PositionTracker.avg_price = 10000
    t.PositionTracker.entry_confidence = 1
    pb.balance = 0.01

    order_metrics = OrderMetrics(
        buy_volume=500,
        sell_volume=1500,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=1,
        imbalance=-0.4
    )

    await t.check_action(order_metrics, 10061)

    assert pb.active_order is not None
    assert pb.active_order.side == ORDER_SELL
    assert pb.active_order.volume == 0.01
    assert pb.active_order.price == 10060


@pytest.mark.asyncio
async def test_trader_hit_stop_losses(with_config):
    with_config.set_value("stop_loss_percentage", 0.05)  # 5% stop loss
    with_config.set_value("stop_loss_offset", 0.05)  # 1% offset
    product = "BTC-USD"
    balance = 1000
    e = MockEvents()
    m = Metrics(product, pe, e) 
    pb = PaperBroker(product, balance, e)
    t = Trader("BTC-USD", pb, m, with_config)
    t.PositionTracker.position = 0.01
    t.PositionTracker.position_cost = 100
    t.PositionTracker.avg_price = 10000
    t.PositionTracker.entry_confidence = 1
    pb.balance = 0.01

    order_metrics = OrderMetrics(
        buy_volume=500,
        sell_volume=1500,
        min_buy=95,
        max_buy=98,
        min_sell=102,
        max_sell=110,
        spread=1,
        imbalance=-0.4
    )

    await t.check_action(order_metrics, 10061)

    assert pb.active_order is not None
    assert pb.active_order.side == ORDER_SELL
    assert pb.active_order.volume == 0.01
    assert pb.active_order.price == 10060
