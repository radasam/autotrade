from pydantic import BaseModel

class OrderUpdate(BaseModel):
    side: str
    price: float
    volume: float