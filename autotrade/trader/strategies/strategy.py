from typing import Protocol

from autotrade.types.order_metrics import OrderMetrics, PriceMetrics
from autotrade.settings.config import Config

class Strategy(Protocol):
    async def get_signals(self, config: Config, order_metrics: OrderMetrics, price_metrics: PriceMetrics) -> tuple[float, float, float]:
        """Calculate trading signals based on the current market state."""
        pass