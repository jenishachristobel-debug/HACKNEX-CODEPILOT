def discount_rate(total: float) -> float:
    if total >= 500:
        return 0.20
    if total >= 100:
        return 0.10
    return 0.0

def final_price(total: float) -> float:
    if total < 0:
        raise ValueError("Total cannot be negative")
    # BUG: negative totals should be rejected.
    return round(total * (1 - discount_rate(total)), 2)
