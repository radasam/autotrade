import pytest

from autotrade.trader.strategies.moving_average import MovingAverageStrategy
from autotrade.types.order_metrics import OrderMetrics, PriceMetrics

@pytest.mark.asyncio
async def test_moving_average_strategy_sensitivity_1(with_config):
    m = MovingAverageStrategy()

    with_config.set_value("moving_average_sensitivity", 100) 
    with_config.set_value("order_price_multiplier", 0.5)

    config = await with_config.get_config()

    order_metrics = OrderMetrics(
        buy_volume=1000,
        sell_volume=500,
        min_buy=10000,
        max_buy=20000,
        min_sell=8000,
        max_sell=15000,
        spread=1000,
        imbalance=0.5
    )
    price_metrics = PriceMetrics(
        price=15000,
        short_moving_average=15000,
        long_moving_average=10000,
        average_true_range=10
    )


    action, confidence, target_price = await m.get_signals(config, order_metrics, price_metrics)

    assert action == 1
    assert confidence == 1.0
    assert target_price == 15015.0 

@pytest.mark.asyncio
async def test_moving_average_strategy_sensitivity_2(with_config):
    m = MovingAverageStrategy()

    with_config.set_value("moving_average_sensitivity", 1000) 
    with_config.set_value("order_price_multiplier", 0.5)

    config = await with_config.get_config()

    order_metrics = OrderMetrics(
        buy_volume=1000,
        sell_volume=500,
        min_buy=10000,
        max_buy=20000,
        min_sell=8000,
        max_sell=15000,
        spread=1000,
        imbalance=0.5
    )
    price_metrics = PriceMetrics(
        price=105,
        short_moving_average=105,
        long_moving_average=100,
        average_true_range=5
    )


    action, confidence, target_price = await m.get_signals(config, order_metrics, price_metrics)

    assert action == 1
    assert confidence == 1.0
    assert target_price == 112.5

@pytest.mark.asyncio
async def test_moving_average_strategy_sell(with_config):
    m = MovingAverageStrategy()

    with_config.set_value("moving_average_sensitivity", 100) 
    with_config.set_value("order_price_multiplier", 0.5)

    config = await with_config.get_config()

    order_metrics = OrderMetrics(
        buy_volume=1000,
        sell_volume=500,
        min_buy=10000,
        max_buy=20000,
        min_sell=8000,
        max_sell=15000,
        spread=1000,
        imbalance=0.5
    )
    price_metrics = PriceMetrics(
        price=100,
        short_moving_average=100,
        long_moving_average=105,
        average_true_range=10
    )


    action, confidence, target_price = await m.get_signals(config, order_metrics, price_metrics)

    assert action == -1
    assert confidence == 1.0
    assert target_price == 85.0 