import pytest
from inventory import Inventory

def test_add_positive_quantity():
    inv = Inventory()
    inv.add("keyboard", 5)
    assert inv.quantity("keyboard") == 5

def test_zero_quantity_is_rejected():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add("keyboard", 0)

def test_remove_exact_stock():
    inv = Inventory()
    inv.add("keyboard", 5)
    inv.remove("keyboard", 5)
    assert inv.quantity("keyboard") == 0

def test_remove_too_much_is_rejected():
    inv = Inventory()
    inv.add("keyboard", 5)
    with pytest.raises(ValueError):
        inv.remove("keyboard", 6)
