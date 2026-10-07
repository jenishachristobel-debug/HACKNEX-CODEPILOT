from auth import is_password_valid, is_token_valid
from datetime import datetime

def login(password: str) -> dict:
    if not is_password_valid(password):
        return {"ok": False, "error": "Invalid password"}
    return {"ok": True}

def validate_token(expires_at: datetime) -> bool:
    return is_token_valid(expires_at, datetime.utcnow())
