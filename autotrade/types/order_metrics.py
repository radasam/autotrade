from pydantic import BaseModel

class OrderMetrics(BaseModel):
    buy_volume: float
    sell_volume: float
    min_buy: float
    max_buy: float
    min_sell: float
    max_sell: float
    spread: float
    imbalance: float

class PriceMetrics(BaseModel):
    price: float = 0
    long_moving_average: float = 0
    short_moving_average: float = 0
    average_true_range: float = 0