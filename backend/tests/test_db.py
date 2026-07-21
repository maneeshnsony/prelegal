import os
import uuid

import pytest
from sqlalchemy import text

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


def test_ensure_database_exists_creates_database_once():
    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    os.environ["DB_DATABASE"] = test_db_name
    try:
        ensure_database_exists()
        ensure_database_exists()  # must be idempotent

        with get_engine("postgres").connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": test_db_name},
            ).scalar()
        assert exists == 1
    finally:
        with get_engine("postgres").connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))
