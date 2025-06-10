from datetime import datetime

from autotrade.types.pending_order import PendingOrder


def test_pending_order_marshal_unmarshal():
    p = PendingOrder(
        side="buy",
        volume=0.01,
        price=10000,
        client_order_id="1234",
        order_id="1234",
        status="OPEN",
        timeout_at=datetime.now(),
    )

    as_str = p.model_dump()

    p2 = PendingOrder(**as_str)

    assert p == p2

    