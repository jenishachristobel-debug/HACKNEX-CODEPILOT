import pytest
from orders import discount_rate, final_price

def test_below_100_has_no_discount():
    assert discount_rate(99.99) == 0.0

def test_exact_100_gets_ten_percent():
    assert discount_rate(100) == 0.10

def test_exact_500_gets_twenty_percent():
    assert discount_rate(500) == 0.20

def test_large_order_gets_twenty_percent():
    assert discount_rate(600) == 0.20

def test_negative_total_is_rejected():
    with pytest.raises(ValueError):
        final_price(-10)
