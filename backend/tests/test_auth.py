import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import ensure_database_exists, get_engine
from app.main import app

client = TestClient(app)


def _postgres_reachable() -> bool:
    try:
        with get_engine("postgres").connect():
            return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_reachable(), reason="Postgres is not reachable from this environment"
)


@pytest.fixture()
def test_engine(monkeypatch):
    import subprocess
    import sys

    import app.routers.auth as auth_module

    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    ensure_database_exists()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )

    engine = get_engine(test_db_name)
    monkeypatch.setattr(auth_module, "engine", engine)

    yield engine

    engine.dispose()

    from sqlalchemy import text

    with get_engine("postgres").connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))


def test_login_creates_user_on_first_call(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/login", json={"email": email})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert isinstance(body["user_id"], int)


def test_login_is_idempotent_for_same_email(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    first = client.post("/api/auth/login", json={"email": email})
    second = client.post("/api/auth/login", json={"email": email})

    assert first.json()["user_id"] == second.json()["user_id"]
