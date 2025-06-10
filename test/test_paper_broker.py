import pytest
from datetime import datetime, timedelta

from autotrade.broker.paper_broker import PaperBroker
from autotrade.events.event_types import EventType, Event
from autotrade.types.broker_error import INSUFFICIENT_FUNDS_ERROR, INSUFFICIENT_PRODUCT_ERROR
from autotrade.types.pending_order import PendingOrder
from autotrade.settings.contants import ORDER_BUY, ORDER_SELL
from test.mocks.events import MockEvents

@pytest.mark.asyncio
async def test_paper_broker_create_limit_order_buy():
    pb = PaperBroker("BTC-USD", 1000, MockEvents())

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

@pytest.mark.asyncio
async def test_paper_broker_create_limit_order_sell():
    pb = PaperBroker("BTC-USD", 1000, MockEvents())
    pb.balance = 0.02

    order, err = await pb.create_limit_order("-0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side== "SELL"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

@pytest.mark.asyncio
async def test_paper_broker_create_limit_order_insufficient_funds():
    pb = PaperBroker("BTC-USD", 1000, MockEvents())
    pb.cash_balance = 0.01

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert order is None
    assert err is not None
    assert err.type == INSUFFICIENT_FUNDS_ERROR

@pytest.mark.asyncio
async def test_paper_broker_create_limit_order_insufficient_product():
    pb = PaperBroker("BTC-USD", 1000, MockEvents())
    pb.balance = 0.01

    order, err = await pb.create_limit_order("-0.02","10000", 0.75, 5)
    assert order is None
    assert err is not None
    assert err.type == INSUFFICIENT_PRODUCT_ERROR

@pytest.mark.asyncio
async def test_paper_broker_create_market_order_buy():
    pb = PaperBroker("BTC-USD", 10000, MockEvents())
    pb.curr_price = 10000

    order, err = await pb.create_market_order("0.01", 0.75)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "FILLED"

@pytest.mark.asyncio
async def test_paper_broker_create_market_order_sell():
    pb = PaperBroker("BTC-USD", 1000, MockEvents())
    pb.curr_price = 10000
    pb.balance = 0.02

    order, err = await pb.create_market_order("-0.01", 0.75)
    assert err is None
    assert order is not None
    assert order.side == "SELL"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "FILLED"

@pytest.mark.asyncio
async def test_paper_broker_limit_buy_filled():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {}
    sells = {10000: 1}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled
    assert pb.active_order.status == "FILLED"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 10000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_BUY,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=10000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.01
    assert pb.cash_balance == 9900.0
    
    
@pytest.mark.asyncio
async def test_paper_broker_limit_buy_partial_filled():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)

    order, err = await pb.create_limit_order("0.05","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.05
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {}
    sells = {10000: 0.01}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled
    assert pb.active_order.status == "OPEN"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 10000

    pb.active_order.timeout_at = datetime.now() - timedelta(seconds=5)

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_BUY,
        price=10000,
        volume=0.05,
        status="CANCELLED",
        filled_size=0.01,
        avg_filled_price=10000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )

    assert pb.active_order is None
    assert len(e.queued_events) == 1
    print(e.queued_events)
    assert e.queued_events[EventType.ORDER_CANCELLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.01
    assert pb.cash_balance == 9900.0
    assert pb.active_order is None
    

@pytest.mark.asyncio
async def test_paper_broker_limit_buy_filled_lower():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {}
    sells = {9000: 1, 10000: 1}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled
    assert pb.active_order.status == "FILLED"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 9000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_BUY,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=9000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.01
    assert pb.cash_balance == 9910.0


@pytest.mark.asyncio
async def test_paper_broker_limit_buy_filled_lower():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {}
    sells = {9000: 1, 10000: 1}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled with the lower price
    assert pb.active_order.status == "FILLED"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 9000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_BUY,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=9000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.01
    assert pb.cash_balance == 9910.0

@pytest.mark.asyncio
async def test_paper_broker_limit_sell_filled():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)
    pb.balance = 0.01

    order, err = await pb.create_limit_order("-0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "SELL"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {10000: 1}
    sells = {}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled with the lower price
    assert pb.active_order.status == "FILLED"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 10000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_SELL,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=10000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0
    assert pb.cash_balance == 10100.0


@pytest.mark.asyncio
async def test_paper_broker_limit_sell_partial_filled():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)
    pb.balance = 0.05

    order, err = await pb.create_limit_order("-0.05","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "SELL"
    assert order.price == 10000
    assert order.volume == 0.05
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {10000: 0.01}
    sells = {}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled with the lower price
    assert pb.active_order.status == "OPEN"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 10000

    pb.active_order.timeout_at = datetime.now() - timedelta(seconds=5)

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_SELL,
        price=10000,
        volume=0.05,
        status="CANCELLED",
        filled_size=0.01,
        avg_filled_price=10000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_CANCELLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.04
    assert pb.cash_balance == 10100.0


@pytest.mark.asyncio
async def test_paper_broker_limit_sell_filled_higher():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)
    pb.balance = 0.01

    order, err = await pb.create_limit_order("-0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "SELL"
    assert order.price == 10000
    assert order.volume == 0.01
    assert order.status == "OPEN"

    # add a sell order to fill the buy order
    buys = {11000:1, 10000: 1}
    sells = {}

    await pb.update_order_book({"buys": buys, "sells": sells})

    # check if the order is filled with the lower price
    assert pb.active_order.status == "FILLED"
    assert pb.active_order.filled_size == 0.01
    assert pb.active_order.avg_filled_price == 11000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_SELL,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=11000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0
    assert pb.cash_balance == 10110.0



@pytest.mark.asyncio
async def test_paper_broker_limit_buy_order_exists():
    e = MockEvents()
    pb = PaperBroker("BTC-USD", 10000, e)

    # add a sell order to fill the buy order
    buys = {}
    sells = {9000: 1, 10000: 1}

    await pb.update_order_book({"buys": buys, "sells": sells})

    order, err = await pb.create_limit_order("0.01","10000", 0.75, 5)
    assert err is None
    assert order is not None
    assert order.side == "BUY"
    assert order.price == 10000
    assert order.volume == 0.01

    # check if the order is filled with the lower price
    assert order.status == "FILLED"
    assert order.filled_size == 0.01
    assert order.avg_filled_price == 9000

    await pb.check_current_order()

    expected_order = PendingOrder(
        side=ORDER_BUY,
        price=10000,
        volume=0.01,
        status="FILLED",
        filled_size=0.01,
        avg_filled_price=9000,
        client_order_id=order.client_order_id,
        order_id=order.order_id,
        timeout_at=order.timeout_at,
        confidence=0.75
    )
    assert pb.active_order is None
    assert len(e.queued_events) == 1
    assert e.queued_events[EventType.ORDER_FILLED][0].value == expected_order.model_dump()

    assert pb.balance == 0.01
    assert pb.cash_balance == 9910.0