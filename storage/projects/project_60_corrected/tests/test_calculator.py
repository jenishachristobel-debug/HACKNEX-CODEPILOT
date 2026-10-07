from calculator import calculate_discount, calculate_shipping, final_price


def test_shipping_calculation():
    assert calculate_shipping(30) == 5.0
    assert calculate_shipping(50) == 0.0
    assert calculate_shipping(100) == 0.0


def test_discount_tier_high():
    assert calculate_discount(150) == 15.0


def test_discount_tier_zero():
    assert calculate_discount(50) == 0.0
