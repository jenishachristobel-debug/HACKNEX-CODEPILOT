from datetime import datetime, timedelta
from auth import is_password_valid, is_token_valid

def test_eight_character_password_is_valid():
    assert is_password_valid("12345678") is True

def test_long_password_is_valid():
    assert is_password_valid("123456789") is True

def test_expired_token_is_invalid():
    now = datetime.utcnow()
    assert is_token_valid(now - timedelta(seconds=1), now) is False

def test_token_at_exact_expiry_is_invalid():
    now = datetime.utcnow()
    assert is_token_valid(now, now) is False
