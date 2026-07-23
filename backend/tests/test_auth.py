import uuid
from concurrent.futures import ThreadPoolExecutor

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
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
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


def test_signup_creates_user_and_returns_token(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert isinstance(body["user_id"], int)
    assert body["token"]


def test_signup_rejects_duplicate_email(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})
    response = client.post("/api/auth/signup", json={"email": email, "password": "different"})
    assert response.status_code == 409


def test_login_succeeds_with_correct_password(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})
    response = client.post("/api/auth/login", json={"email": email, "password": "hunter22"})
    assert response.status_code == 200
    assert response.json()["token"]


def test_login_rejects_wrong_password(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})
    response = client.post("/api/auth/login", json={"email": email, "password": "wrong"})
    assert response.status_code == 401


def test_login_rejects_unknown_email(test_engine):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert response.status_code == 401


def test_concurrent_signup_same_email_never_returns_500(test_engine):
    email = f"{uuid.uuid4().hex[:8]}@example.com"

    def do_signup():
        return client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [f.result() for f in [executor.submit(do_signup), executor.submit(do_signup)]]

    statuses = sorted(r.status_code for r in results)
    assert statuses == [200, 409]
