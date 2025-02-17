import logging

from autotrade.metrics.metrics import Metrics

class PaperBroker():

    def __init__(self, starting_balance: float, metrics: Metrics):
        self.balance = starting_balance
        self.metrics = metrics
        pass

    def buy(self, product: str, volume: float):
        cost = self.metrics.products[product].market_price * volume

        if cost > self.balance:
            logging.error("")

        pass