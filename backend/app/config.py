import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "backend" / ".env")


def resolve_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if raw_url:
        return raw_url

    db_user = os.getenv("DB_USER", "codepilot_user")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "codepilot_db")

    if db_password:
        encoded_password = quote_plus(db_password)
        return f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"

    return f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}"


class Settings(BaseModel):
    PROJECT_NAME: str = "CodePilot AI"
    VERSION: str = "1.0.0-hackathon"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = resolve_database_url()
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "")

    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    PROJECTS_DIR: Path = STORAGE_DIR / "projects"
    SANDBOX_DIR: Path = STORAGE_DIR / "sandboxes"

    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "safe_local")
    MAX_REPAIR_ATTEMPTS: int = int(os.getenv("MAX_REPAIR_ATTEMPTS", "2"))
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024
    MAX_ARCHIVE_SIZE_BYTES: int = 25 * 1024 * 1024
    MAX_EXTRACTED_SIZE_BYTES: int = 50 * 1024 * 1024
    MAX_EXTRACTED_FILES: int = 500
    TEST_TIMEOUT_SECONDS: int = 30


settings = Settings()

settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

