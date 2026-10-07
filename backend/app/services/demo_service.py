import io
import zipfile
from pathlib import Path
from typing import Dict, Tuple

DEMO_PROJECT_NAME = "ShopPilot Pricing Engine"
DEMO_BUG_TITLE = "Orders of exactly $100 fail to receive Tier-1 discount"
DEMO_BUG_DESC = "Customer orders of exactly $100.00 receive $0.0 discount instead of the expected 10% ($10.00). The boundary check `total > 100` mistakenly excludes the $100.00 threshold."
DEMO_TRACEBACK = "AssertionError: assert calculate_discount(100.0) == 10.0, got 0.0\n  File 'tests/test_calculator.py', line 18, in test_discount_boundary"
DEMO_EXPECTED = "calculate_discount(100.0) returns 10.0 with all existing shipping and tier tests continuing to pass."


def create_demo_zip() -> bytes:
    """Generates an in-memory ZIP archive of the demo pricing engine project."""
    repo_files = {
        "calculator.py": '''"""
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
    if total > 100:
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
''',
        "app.py": '''"""
ShopPilot Checkout Service
Processes customer carts and applies pricing rules.
"""
from calculator import final_price


def process_order(customer_name: str, item_prices: list) -> dict:
    total = sum(item_prices)
    amount_due = final_price(total)
    return {
        "customer": customer_name,
        "items_count": len(item_prices),
        "subtotal": round(total, 2),
        "final_price": amount_due
    }
''',
        "tests/test_calculator.py": '''from calculator import calculate_discount, calculate_shipping, final_price


def test_shipping_calculation():
    assert calculate_shipping(30) == 5.0
    assert calculate_shipping(50) == 0.0
    assert calculate_shipping(100) == 0.0


def test_discount_tier_high():
    assert calculate_discount(150) == 15.0


def test_discount_tier_zero():
    assert calculate_discount(50) == 0.0
''',
        "tests/test_app.py": '''from app import process_order


def test_process_order_basic():
    order = process_order("Alice", [20.0, 30.0])
    assert order["customer"] == "Alice"
    assert order["subtotal"] == 50.0
    assert order["final_price"] == 50.0
'''
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in repo_files.items():
            zf.writestr(filepath, content)
    buf.seek(0)
    return buf.getvalue()
