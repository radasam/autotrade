from autotrade.types.order_metrics import OrderMetrics, PriceMetrics
from autotrade.settings.config import Config

class OrderImbalanceStrategy:
    def __init__(self):
        return

    async def get_signals(self, config: Config, order_metrics: OrderMetrics, price_metrics: PriceMetrics) -> tuple[float, float, float]:

        imbalance = order_metrics.imbalance
        spread = order_metrics.spread
        spread_pct = abs(spread) / price_metrics.price

        if imbalance >= config.imbalance_threshold and spread_pct <= config.spread_threshold:
            # Strong buy pressure with acceptable spread
            action = 1
            confidence = min(1.0, imbalance * 2)
        elif imbalance <= -config.imbalance_threshold and spread_pct <= config.spread_threshold:
            # Strong sell pressure with acceptable spread
            action = -1
            confidence = min(1.0, abs(imbalance) * 2)
        else:
            # No strong signal or spread too wide
            action = 0
            confidence = 0
        
        target_price = spread * action * confidence * config.order_price_multiplier

        return action, confidence, target_price