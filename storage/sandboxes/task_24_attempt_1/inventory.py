class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, name: str, quantity: int):
        # BUG: zero should be rejected.
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.items[name] = self.items.get(name, 0) + quantity

    def remove(self, name: str, quantity: int):
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        current = self.items.get(name, 0)

        # BUG: removing exactly all available stock should be allowed.
        if quantity > current:
            raise ValueError("not enough stock")

        self.items[name] = current - quantity

    def quantity(self, name: str) -> int:
        return self.items.get(name, 0)
