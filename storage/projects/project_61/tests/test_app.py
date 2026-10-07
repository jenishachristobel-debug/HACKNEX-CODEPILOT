from app import process_order


def test_process_order_basic():
    order = process_order("Alice", [20.0, 30.0])
    assert order["customer"] == "Alice"
    assert order["subtotal"] == 50.0
    assert order["final_price"] == 50.0
