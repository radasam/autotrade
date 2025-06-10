from math import tanh

from autotrade.types.order_metrics import OrderMetrics, PriceMetrics
from autotrade.settings.config import Config

class MovingAverageStrategy:
    def __init__(self):
        return

    async def get_signals(self, config: Config, order_metrics: OrderMetrics, price_metrics: PriceMetrics) -> tuple[float, float, float]:

        slope = (price_metrics.short_moving_average - price_metrics.long_moving_average) / price_metrics.long_moving_average
        confidence = round(abs(tanh(slope * config.moving_average_sensitivity)),2)

        target_distance = abs(price_metrics.average_true_range * (1 + confidence * config.order_price_multiplier))

        if price_metrics.short_moving_average > price_metrics.long_moving_average:
            return 1, confidence, round(price_metrics.price + target_distance, 2)
        elif price_metrics.short_moving_average < price_metrics.long_moving_average:
            return -1, confidence, round(price_metrics.price - target_distance)
        else:
            return 0, 0, 0