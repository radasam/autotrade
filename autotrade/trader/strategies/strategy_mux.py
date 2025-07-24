from typing import Dict

from autotrade.types.order_metrics import OrderMetrics, PriceMetrics
from autotrade.trader.strategies.strategy import Strategy
from autotrade.settings.config import ConfigGetter, Config


class SignalTracker:
    def __init__(self):
        self.curr_action = 0
        self.action_count = 0
        pass

    def update(self, action: int):
        if action == self.curr_action:
            self.action_count += 1
        else:
            self.curr_action = action
            self.action_count = 1
    
    def get_signal(self, min_buy_signals: int, min_sell_signals: int):
        if self.curr_action == 1 and self.action_count >= min_buy_signals:
            return 1
        elif self.curr_action == -1 and self.action_count >= min_sell_signals:
            return -1
        else:
            return 0

class StrategyMux:
    """
    StrategyMux is a class that allows for the multiplexing of multiple trading strategies.
    """

    def __init__(self, config_getter: ConfigGetter) -> None:
        self.strategies: Dict[str, Strategy] = {}
        self.config_getter = config_getter 
        self.curr_action = 0
        self.action_count = 0 

    def update_signal(self, action: int) -> None:
        """
        Update the current action and action count based on the provided action.
        """
        if action == self.curr_action:
            self.action_count += 1
        else:
            self.curr_action = action
            self.action_count = 1

    def check_signal(self, config: Config) -> int:
        """
        Check the current action and action count to determine the trading signal.
        Returns:
            1 if a strong buy signal is detected,
            -1 if a strong sell signal is detected,
            0 otherwise.
        """
        if self.curr_action == 1 and self.action_count >= config.min_signals_for_buy_action:
            return 1
        elif self.curr_action == -1 and self.action_count >= config.min_signals_for_sell_action:
            return -1
        else:
            return 0


    def register_strategy(self, strategy:  Strategy, name: str = None) -> None:
        """
        Register a new strategy to the mux.
        """
        self.strategies[name] = strategy


    async def get_signals(self, order_metrics: OrderMetrics, price_metrics: PriceMetrics) -> tuple[float, float, float]:

        config_value = await self.config_getter.get_config()


        strategy = self.strategies.get(config_value.strategy)
        if strategy:
            action, confidence, price = await strategy.get_signals(config_value, order_metrics, price_metrics)

            if confidence < config_value.min_confidence_for_action:
                self.update_signal(0)
                return 0, confidence, 0
                
            self.update_signal(action)
            return self.check_signal(config_value), confidence, price
        
        raise ValueError(f"Strategy {config_value.strategy} not found in registered strategies.")



