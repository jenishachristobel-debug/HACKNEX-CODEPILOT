import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import settings, BASE_DIR
from app.database import engine, Base
import app.models

def parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        # SQLite stores 'YYYY-MM-DD HH:MM:SS.ffffff' or 'YYYY-MM-DDTHH:MM:SS'
        val_clean = str(val).replace('T', ' ')
        if '.' in val_clean:
            return datetime.strptime(val_clean, '%Y-%m-%d %H:%M:%S.%f')
        return datetime.strptime(val_clean, '%Y-%m-%d %H:%M:%S')
    except Exception:
        try:
            return datetime.fromisoformat(str(val))
        except Exception:
            return datetime.utcnow()

def migrate_data():
    sqlite_path = BASE_DIR / 'codepilot.db'
    if not sqlite_path.exists():

        print(f'SQLite database not found at {sqlite_path}. Nothing to migrate.')
        return

    safe_target = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
    print(f'Checking migration from {sqlite_path} to MySQL: {safe_target}')
    
    # 1. Ensure MySQL tables exist
    Base.metadata.create_all(bind=engine)

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    s_cur = sqlite_conn.cursor()

    Session = sessionmaker(bind=engine)
    mysql_session = Session()

    def table_is_empty(table_name: str) -> bool:
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() == 0

    try:
        # 1. Projects
        if table_is_empty("projects"):
            s_cur.execute('SELECT * FROM projects')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                d['updated_at'] = parse_dt(d.get('updated_at'))
                proj = app.models.Project(**d)
                mysql_session.add(proj)
            mysql_session.commit()
            print('Migrated projects table successfully.')
        else:
            print('Projects table already contains data, skipping.')

        # 2. Repository Scans
        if table_is_empty("repository_scans"):
            s_cur.execute('SELECT * FROM repository_scans')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                scan = app.models.RepositoryScan(**d)
                mysql_session.add(scan)
            mysql_session.commit()
            print('Migrated repository_scans table successfully.')
        else:
            print('Repository scans table already contains data, skipping.')

        # 3. Tasks
        if table_is_empty("tasks"):
            s_cur.execute('SELECT * FROM tasks')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                d['updated_at'] = parse_dt(d.get('updated_at'))
                task = app.models.Task(**d)
                mysql_session.add(task)
            mysql_session.commit()
            print('Migrated tasks table successfully.')
        else:
            print('Tasks table already contains data, skipping.')

        # 4. Analysis Results
        if table_is_empty("analysis_results"):
            s_cur.execute('SELECT * FROM analysis_results')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                d['is_llm_generated'] = bool(d.get('is_llm_generated', 0))
                ar = app.models.AnalysisResult(**d)
                mysql_session.add(ar)
            mysql_session.commit()
            print('Migrated analysis_results table successfully.')
        else:
            print('Analysis results table already contains data, skipping.')

        # 5. Patches
        if table_is_empty("patches"):
            s_cur.execute('SELECT * FROM patches')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                p = app.models.Patch(**d)
                mysql_session.add(p)
            mysql_session.commit()
            print('Migrated patches table successfully.')
        else:
            print('Patches table already contains data, skipping.')

        # 6. Test Runs
        if table_is_empty("test_runs"):
            s_cur.execute('SELECT * FROM test_runs')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                tr = app.models.TestRun(**d)
                mysql_session.add(tr)
            mysql_session.commit()
            print('Migrated test_runs table successfully.')
        else:
            print('Test runs table already contains data, skipping.')

        # 7. Verification Reports
        if table_is_empty("verification_reports"):
            s_cur.execute('SELECT * FROM verification_reports')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                vr = app.models.VerificationReport(**d)
                mysql_session.add(vr)
            mysql_session.commit()
            print('Migrated verification_reports table successfully.')
        else:
            print('Verification reports table already contains data, skipping.')

        # 8. Fix History
        if table_is_empty("fix_history"):
            s_cur.execute('SELECT * FROM fix_history')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                fh = app.models.FixHistory(**d)
                mysql_session.add(fh)
            mysql_session.commit()
            print('Migrated fix_history table successfully.')
        else:
            print('Fix history table already contains data, skipping.')

        # 9. Audit Logs
        if table_is_empty("audit_logs"):
            s_cur.execute('SELECT * FROM audit_logs')
            for r in s_cur.fetchall():
                d = dict(r)
                d['created_at'] = parse_dt(d.get('created_at'))
                al = app.models.AuditLog(**d)
                mysql_session.add(al)
            mysql_session.commit()
            print('Migrated audit_logs table successfully.')
        else:
            print('Audit logs table already contains data, skipping.')

        print('ALL SQLite records migrated into MySQL successfully!')

    except Exception as e:
        mysql_session.rollback()
        print(f'Error during migration: {e}')
        raise
    finally:
        mysql_session.close()
        sqlite_conn.close()

if __name__ == '__main__':
    migrate_data()
