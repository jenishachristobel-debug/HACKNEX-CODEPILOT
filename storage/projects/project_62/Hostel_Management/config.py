import os
from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv()

class Config:
    """Application configuration supporting Supabase PostgreSQL and local fallback."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'hostel_jwt_session_secret_key_2026')
    
    # -------------------------------------------------------------
    # Supabase Connection Settings
    # -------------------------------------------------------------
    # Option 1: Direct PostgreSQL URI (from Supabase Database settings)
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    # Option 2: Supabase REST API credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '') or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

    # Option 3: Individual Connection Parameters
    DB_HOST = os.getenv('DB_HOST', '')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'postgres')

    # SQLite Fallback path if Supabase connection is pending or offline
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hostel_dev.db')
