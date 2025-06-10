
INSUFFICIENT_FUNDS_ERROR = "InsufficientFundsError"
INSUFFICIENT_PRODUCT_ERROR = "InsufficientProductError"
REQUEST_ERROR = "RequestError"
EXISTING_ORDER_ERROR = "ExistingOrderError"

class BrokerError(Exception):
    def __init__(self, type:str, message: str):
        self.type = type
        self.message = message

    def __str__(self):
        return self.message
    
def existing_order_error(order_id: str) -> BrokerError:
    return BrokerError("ExistingOrderError", f"Already have an active order {order_id}")

def insufficient_funds_error(product: str, volume: float, price: float, cash_balance: float) -> BrokerError:
    return BrokerError("InsufficientFundsError", f"Insufficient funds to purchase {volume} of {product} at {price} for {volume*price} balance is {cash_balance}")

def insufficient_product_error(product: str, volume: float, balance: float) -> BrokerError:
    return BrokerError("InsufficientProductError", f"Insufficient {product} to sell {volume}, balance is {balance}")

def request_error(message: str) -> BrokerError:
    return BrokerError("RequestError", message)