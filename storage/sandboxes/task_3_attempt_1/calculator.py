"""
ShopPilot Pricing Engine
Calculates promotional discounts and shipping charges.
"""

def calculate_discount(total: float) -> float:
    """
    Tier-1 promotional discount:
    - Orders >= 100 get 10% discount
    - Orders < 100 get 0% discount
    """
    # BUG: uses > 100 instead of >= 100
    if total >= 100:
        return round(total * 0.10, 2)
    return 0.0


def calculate_shipping(total: float) -> float:
    """Free shipping on orders >= $50, else $5.00 flat rate."""
    if total >= 50:
        return 0.0
    return 5.0


def final_price(total: float) -> float:
    discount = calculate_discount(total)
    shipping = calculate_shipping(total)
    return round(total - discount + shipping, 2)
