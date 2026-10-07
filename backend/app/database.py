import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("codepilot.database")

# Build engine with MySQL-appropriate pooling or SQLite fallbacks
if "mysql" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_schema_columns(target_engine=None):
    active_engine = target_engine or engine
    migrations = [
        ("repository_scans", "manifest_json", "LONGTEXT"),
        ("repository_scans", "inventory_json", "LONGTEXT"),
        ("repository_scans", "dependency_graph_json", "LONGTEXT"),
        ("analysis_results", "call_path", "TEXT"),
        ("analysis_results", "expected_behavior", "LONGTEXT"),
        ("analysis_results", "actual_behavior", "LONGTEXT"),
        ("analysis_results", "proposed_fix", "LONGTEXT"),
        ("projects", "corrected_storage_path", "VARCHAR(500) NULL"),
        ("verification_reports", "integrity_check_json", "LONGTEXT"),
        ("test_runs", "skipped_count", "INT DEFAULT 0"),
        ("test_runs", "stdout", "LONGTEXT"),
        ("test_runs", "stderr", "LONGTEXT"),
    ]
    with active_engine.begin() as conn:
        for table, col, col_type in migrations:
            try:
                if "mysql" in active_engine.dialect.name:
                    check = conn.execute(text(f"SHOW COLUMNS FROM {table} LIKE '{col}'")).fetchone()
                    if not check:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        logger.info(f"[MIGRATION] Added column {table}.{col}")
                elif "sqlite" in active_engine.dialect.name:
                    check = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                    existing_cols = [c[1] for c in check]
                    if col not in existing_cols:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
            except Exception as e:
                logger.warning(f"[MIGRATION] Column ensure check for {table}.{col}: {e}")


def init_db():
    # 1. Connection health verification - fail fast if MySQL is unreachable
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[DATABASE] Verified connection to database successfully.")
    except Exception as exc:
        safe_url = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        logger.error("[DATABASE ERROR] Failed to connect to database (%s): %s", safe_url, exc)
        raise RuntimeError(
            f"Database connection failed for target [{safe_url}]. "
            f"Ensure MySQL service is running and credentials are valid: {exc}"
        ) from exc

    # 2. Import all models to register with Base.metadata
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)

    # 3. Ensure any new columns exist in MySQL / SQLite schema
    _ensure_schema_columns()

    # 4. Migrate SQLite historical data if MySQL is freshly initialized
    try:
        from app.scripts.migrate_sqlite_to_mysql import migrate_data
        migrate_data()
    except Exception as exc:
        logger.warning("[MIGRATION WARNING] SQLite migration check skipped or encountered error: %s", exc)

