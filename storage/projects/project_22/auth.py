from datetime import datetime, timedelta

TOKEN_LIFETIME_MINUTES = 30

def create_token(user_id: int) -> dict:
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_LIFETIME_MINUTES)
    return {"user_id": user_id, "expires_at": expires_at.isoformat()}

def is_password_valid(password: str) -> bool:
    # BUG: passwords of exactly 8 characters should be accepted.
    return len(password) > 8

def is_token_valid(expires_at: datetime, now: datetime) -> bool:
    # BUG: a token at the exact expiry instant should be considered expired.
    return now > expires_at
