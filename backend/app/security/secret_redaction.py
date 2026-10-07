import re

SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z-_]{35}",  # Google API keys
    r"sk-[a-zA-Z0-9]{20,}",    # OpenAI API keys
    r"ghp_[a-zA-Z0-9]{36}",    # GitHub personal tokens
    r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", # Generic Bearer tokens
    r"['\"]?(?:api[_-]?key|secret|token|password)['\"]?\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SECRET_PATTERNS]


def redact_secrets(text: str) -> str:
    """
    Scans a given text or log string and redacts potential API keys, credentials, and passwords.
    """
    if not text:
        return ""

    sanitized = text
    for pattern in COMPILED_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)

    return sanitized

