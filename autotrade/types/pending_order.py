from pydantic import BaseModel
from typing import Union
from datetime import datetime
from enum import Enum

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class PendingOrder(BaseModel):
    order_type: OrderType  # e.g., "market", "limit"
    side: str
    volume: float
    price: float
    order_id: str
    client_order_id: str
    status: str
    timeout_at: Union[datetime, None] = None
    filled_size: float = 0
    avg_filled_price: float = 0
    confidence: float = 0