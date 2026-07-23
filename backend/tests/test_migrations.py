import subprocess
import sys
import uuid

import pytest
from sqlalchemy import inspect, text

from app.db import ensure_database_exists, get_engine


def _postgres_reachable() -> bool:
    try:
        with get_engine("postgres").connect():
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_reachable(), reason="Postgres is not reachable from this environment"
)


def test_migration_creates_users_table(monkeypatch):
    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    ensure_database_exists()
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=True,
        )
        test_engine = get_engine(test_db_name)
        inspector = inspect(test_engine)
        columns = {col["name"] for col in inspector.get_columns("users")}
        test_engine.dispose()
        assert columns == {"id", "email", "password_hash", "created_at"}
    finally:
        with get_engine("postgres").connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))
