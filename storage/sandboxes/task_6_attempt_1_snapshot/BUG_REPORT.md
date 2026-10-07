# Authentication API Bug

1. Exactly 8-character passwords should be accepted.
2. A token at its exact expiry timestamp must be considered expired.

Run `pytest -q` to reproduce.
