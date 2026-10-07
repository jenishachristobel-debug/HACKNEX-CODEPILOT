import os
import sqlite3
import psycopg2
import psycopg2.extras
from config import Config

# Supabase Client import
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

_USE_SQLITE_FALLBACK = False
_SUPABASE_CLIENT = None

def get_supabase_client():
    """Initializes and returns the Supabase REST Client if keys are configured."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT:
        return _SUPABASE_CLIENT

    if Config.SUPABASE_URL and Config.SUPABASE_KEY and create_client:
        try:
            _SUPABASE_CLIENT = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            return _SUPABASE_CLIENT
        except Exception:
            return None
    return None

def get_postgres_connection():
    """Attempt to establish direct PostgreSQL connection to Supabase."""
    try:
        if Config.DATABASE_URL:
            conn = psycopg2.connect(Config.DATABASE_URL)
            return conn
        elif Config.DB_HOST and Config.DB_PASSWORD:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            return conn
        return None
    except Exception:
        return None

def test_db_connection():
    """Checks whether Supabase PostgreSQL or API is working, otherwise falls back to SQLite."""
    global _USE_SQLITE_FALLBACK
    
    # 1. Test direct PostgreSQL connection
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cur = pg_conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
            pg_conn.close()
            _USE_SQLITE_FALLBACK = False
            return "supabase_postgres"
        except Exception:
            pass

    # 2. Test Supabase API Client
    client = get_supabase_client()
    if client:
        try:
            client.table('students').select('*').limit(1).execute()
            return "supabase_api"
        except Exception:
            pass

    _USE_SQLITE_FALLBACK = True
    return "sqlite"

def get_connection():
    """Returns an active database connection with cursor support (PostgreSQL or SQLite)."""
    global _USE_SQLITE_FALLBACK
    if not _USE_SQLITE_FALLBACK:
        pg_conn = get_postgres_connection()
        if pg_conn:
            return pg_conn, "supabase_postgres"

    # SQLite connection fallback
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, "sqlite"

def execute_query(query, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query and commits.
    Returns dictionary with lastrowid and rowcount.
    """
    conn, engine = get_connection()
    try:
        if engine == "supabase_postgres":
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            trimmed = query.strip()
            is_insert = trimmed.upper().startswith("INSERT")
            if is_insert and "RETURNING" not in trimmed.upper():
                trimmed = trimmed.rstrip(";") + " RETURNING *"

            cursor.execute(trimmed, params or ())
            last_id = None
            if is_insert:
                try:
                    row = cursor.fetchone()
                    if row:
                        for key in row.keys():
                            if 'id' in key.lower():
                                last_id = row[key]
                                break
                        if last_id is None and len(row) > 0:
                            last_id = list(row.values())[0]
                except Exception:
                    pass

            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return {"lastrowid": last_id, "rowcount": affected}
        else:
            # SQLite adaptation: replace %s with ?
            sqlite_query = query.replace("%s", "?")
            cursor = conn.cursor()
            cursor.execute(sqlite_query, params or ())
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return {"lastrowid": last_id, "rowcount": affected}
    except Exception as e:
        if engine == "supabase_postgres" and conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        elif engine == "sqlite" and conn:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
        raise e

def fetch_all(query, params=None):
    """Executes a SELECT query and returns all matching rows as a list of dicts."""
    conn, engine = get_connection()
    try:
        if engine == "supabase_postgres":
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params or ())
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return results
        else:
            sqlite_query = query.replace("%s", "?")
            cursor = conn.cursor()
            cursor.execute(sqlite_query, params or ())
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            cursor.close()
            conn.close()
            return results
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        raise e

def fetch_one(query, params=None):
    """Executes a SELECT query and returns a single matching row as a dict."""
    conn, engine = get_connection()
    try:
        if engine == "supabase_postgres":
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            result = dict(row) if row else None
            cursor.close()
            conn.close()
            return result
        else:
            sqlite_query = query.replace("%s", "?")
            cursor = conn.cursor()
            cursor.execute(sqlite_query, params or ())
            row = cursor.fetchone()
            result = dict(row) if row else None
            cursor.close()
            conn.close()
            return result
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        raise e
