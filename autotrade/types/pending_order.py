from pydantic import BaseModel
from typing import Union
from datetime import datetime

class PendingOrder(BaseModel):
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