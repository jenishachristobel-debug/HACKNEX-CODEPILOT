import os
import sys
from pathlib import Path
from urllib.parse import quote_plus
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
import app.models
from app.database import Base, get_db
import app.database
from app.main import app as fastapi_app

test_db_url = settings.TEST_DATABASE_URL or os.getenv("TEST_DATABASE_URL")
if not test_db_url:
    db_user = os.getenv("DB_USER", "codepilot_user")
    db_password = os.getenv("DB_PASSWORD", "Jeni@2007")
    test_db_url = f"mysql+pymysql://{db_user}:{quote_plus(db_password)}@127.0.0.1:3306/codepilot_test_db"

test_engine = create_engine(test_db_url, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Point app.database engine and SessionLocal to test database
app.database.engine = test_engine
app.database.SessionLocal = TestSessionLocal

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Verify connection to MySQL test database
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    Base.metadata.create_all(bind=test_engine)
    app.database._ensure_schema_columns(test_engine)
    yield

