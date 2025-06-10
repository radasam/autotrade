from enum import Enum

from autotrade.types.order_metrics import OrderMetrics

class EventType(Enum):
    ORDER_UPDATE = "order_update"
    ORDER_BOOK_UPDATE = "order_book_update"
    PRICE_UPDATE = "price_update"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"

class Event:
    def __init__(self, event_type: EventType, value):
        self.event_type = event_type
        self.value = value