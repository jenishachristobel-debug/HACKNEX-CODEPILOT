# Inventory Bug

- Adding quantity 0 must be rejected.
- Removing exactly the current stock must be allowed.
- Removing more than current stock must be rejected.

Run `pytest -q`.
