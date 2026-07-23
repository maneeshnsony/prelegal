import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db import ensure_database_exists, get_engine
from app.llm import IntakeTurn
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
def test_db(monkeypatch):
    import subprocess
    import sys

    import app.routers.auth as auth_module
    import app.routers.documents as documents_module

    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-key-thats-long-enough")
    ensure_database_exists()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )

    engine = get_engine(test_db_name)
    monkeypatch.setattr(auth_module, "engine", engine)
    monkeypatch.setattr(documents_module, "engine", engine)

    yield engine

    engine.dispose()

    from sqlalchemy import text

    with get_engine("postgres").connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))


def _signup(email: str | None = None) -> dict:
    email = email or f"{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/signup", json={"email": email, "password": "hunter22"})
    return response.json()


@pytest.fixture()
def auth_headers(test_db):
    token = _signup()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def other_auth_headers(test_db):
    token = _signup()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_can_create_multiple_drafts(auth_headers):
    first = client.post("/api/documents", headers=auth_headers).json()
    second = client.post("/api/documents", headers=auth_headers).json()
    assert first["id"] != second["id"]


def test_list_documents_returns_only_callers_drafts(auth_headers, other_auth_headers):
    client.post("/api/documents", headers=auth_headers)
    client.post("/api/documents", headers=other_auth_headers)
    response = client.get("/api/documents", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_cannot_access_another_users_draft(auth_headers, other_auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    response = client.get(f"/api/documents/{draft['id']}", headers=other_auth_headers)
    assert response.status_code == 404


def test_new_draft_has_no_document_type(auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    response = client.get(f"/api/documents/{draft['id']}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] is None
    assert body["fields"] == {}
    assert body["messages"] == []


def test_chat_with_clear_request_sets_document_type(auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    canned = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Let's set up your NDA.")

    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        response = client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "I need an NDA"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert body["reply"] == canned.reply


def test_chat_with_unsupported_request_suggests_closest_without_setting_type(auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    canned = IntakeTurn(
        document_type=None,
        suggested_document_type="Software-License-Agreement",
        reply="We can't generate that, but how about a Software License Agreement?",
    )

    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        response = client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "I need an employment contract"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] is None


def test_chat_after_document_type_chosen_uses_field_turn(auth_headers):
    from app.document_types import build_field_turn_model

    draft = client.post("/api/documents", headers=auth_headers).json()
    intake = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Great, let's begin.")
    with patch("app.routers.documents.run_intake_turn", return_value=intake):
        client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "I need an NDA"},
            headers=auth_headers,
        )

    Model = build_field_turn_model("Mutual-NDA")
    field_turn = Model(party_a_name="Acme Inc.", reply="And Party B?")
    with patch("app.routers.documents.run_field_turn", return_value=field_turn):
        response = client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "Acme Inc."},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert body["fields"]["party_a_name"] == "Acme Inc."

    fetched = client.get(f"/api/documents/{draft['id']}", headers=auth_headers).json()
    assert fetched["fields"]["party_a_name"] == "Acme Inc."


def test_list_marks_draft_complete_once_all_fields_filled(auth_headers):
    from app.document_types import DOCUMENT_TYPES, build_field_turn_model

    draft = client.post("/api/documents", headers=auth_headers).json()
    intake = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Great, let's begin.")
    with patch("app.routers.documents.run_intake_turn", return_value=intake):
        client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "I need an NDA"},
            headers=auth_headers,
        )

    Model = build_field_turn_model("Mutual-NDA")
    all_fields = {f.field_id: f"value-{f.field_id}" for f in DOCUMENT_TYPES["Mutual-NDA"].fields}
    field_turn = Model(reply="All set!", **all_fields)
    with patch("app.routers.documents.run_field_turn", return_value=field_turn):
        client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "here is everything"},
            headers=auth_headers,
        )

    listing = client.get("/api/documents", headers=auth_headers).json()
    matching = next(d for d in listing if d["id"] == draft["id"])
    assert matching["is_complete"] is True


def test_render_endpoint_returns_409_before_document_type_chosen(auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    response = client.get(f"/api/documents/{draft['id']}/render", headers=auth_headers)
    assert response.status_code == 409


def test_render_endpoint_returns_paragraphs_after_document_type_chosen(auth_headers):
    draft = client.post("/api/documents", headers=auth_headers).json()
    canned = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Let's begin.")
    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        client.post(
            f"/api/documents/{draft['id']}/chat",
            json={"message": "I need an NDA"},
            headers=auth_headers,
        )

    response = client.get(f"/api/documents/{draft['id']}/render", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert len(body["paragraphs"]) > 0
