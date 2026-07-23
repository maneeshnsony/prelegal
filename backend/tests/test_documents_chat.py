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
def user_id(monkeypatch):
    import subprocess
    import sys

    import app.routers.auth as auth_module
    import app.routers.documents as documents_module

    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    ensure_database_exists()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )

    engine = get_engine(test_db_name)
    monkeypatch.setattr(auth_module, "engine", engine)
    monkeypatch.setattr(documents_module, "engine", engine)

    email = f"{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/login", json={"email": email})
    yield response.json()["user_id"]

    engine.dispose()

    from sqlalchemy import text

    with get_engine("postgres").connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))


def test_new_draft_has_no_document_type(user_id):
    response = client.get("/api/documents/draft", params={"user_id": user_id})

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] is None
    assert body["fields"] == {}
    assert body["messages"] == []


def test_chat_with_clear_request_sets_document_type(user_id):
    canned = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Let's set up your NDA.")

    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        response = client.post(
            "/api/documents/chat", json={"user_id": user_id, "message": "I need an NDA"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert body["reply"] == canned.reply


def test_chat_with_unsupported_request_suggests_closest_without_setting_type(user_id):
    canned = IntakeTurn(
        document_type=None,
        suggested_document_type="Software-License-Agreement",
        reply="We can't generate that, but how about a Software License Agreement?",
    )

    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        response = client.post(
            "/api/documents/chat",
            json={"user_id": user_id, "message": "I need an employment contract"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] is None
    assert "reply" in body


def test_chat_after_document_type_chosen_uses_field_turn(user_id):
    from app.document_types import build_field_turn_model

    intake = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Great, let's begin.")
    with patch("app.routers.documents.run_intake_turn", return_value=intake):
        client.post("/api/documents/chat", json={"user_id": user_id, "message": "I need an NDA"})

    Model = build_field_turn_model("Mutual-NDA")
    field_turn = Model(party_a_name="Acme Inc.", reply="And Party B?")
    with patch("app.routers.documents.run_field_turn", return_value=field_turn):
        response = client.post(
            "/api/documents/chat", json={"user_id": user_id, "message": "Acme Inc."}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert body["fields"]["party_a_name"] == "Acme Inc."

    draft = client.get("/api/documents/draft", params={"user_id": user_id}).json()
    assert draft["fields"]["party_a_name"] == "Acme Inc."


def test_render_endpoint_returns_409_before_document_type_chosen(user_id):
    response = client.get("/api/documents/draft/render", params={"user_id": user_id})
    assert response.status_code == 409


def test_render_endpoint_returns_paragraphs_after_document_type_chosen(user_id):
    canned = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Let's begin.")
    with patch("app.routers.documents.run_intake_turn", return_value=canned):
        client.post("/api/documents/chat", json={"user_id": user_id, "message": "I need an NDA"})

    response = client.get("/api/documents/draft/render", params={"user_id": user_id})
    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "Mutual-NDA"
    assert len(body["paragraphs"]) > 0
