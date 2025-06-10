from autotrade.broker.api_broker import APIBroker

broker = APIBroker("BTC-GBP")

if __name__ == "__main__":
    # orders = broker.list_orders()
    # print(orders)

    # client_order_id, order_id, err = broker.create_market_order("BTC-USD", "SELL", "0.01", "1")
    # broker.create_limit_order("BTC-USD", "SELL", "0.01", "1", 10000)

    print(broker.get_product_details())