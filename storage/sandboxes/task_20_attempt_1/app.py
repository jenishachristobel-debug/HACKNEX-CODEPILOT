"""
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
