import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db import ensure_database_exists, get_engine
from app.llm import NdaChatTurn
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
    import app.routers.nda as nda_module

    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    ensure_database_exists()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
    )

    engine = get_engine(test_db_name)
    monkeypatch.setattr(auth_module, "engine", engine)
    monkeypatch.setattr(nda_module, "engine", engine)

    email = f"{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/api/auth/login", json={"email": email})
    yield response.json()["user_id"]

    engine.dispose()

    from sqlalchemy import text

    with get_engine("postgres").connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))


def test_get_draft_creates_draft_with_opening_message(user_id):
    response = client.get("/api/nda/draft", params={"user_id": user_id})

    assert response.status_code == 200
    body = response.json()
    assert body["fields"]["partyAName"] == ""
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "assistant"


def test_chat_persists_messages_and_updates_fields(user_id):
    canned_turn = NdaChatTurn(
        party_a_name="Acme Inc.",
        party_b_name="Globex Corporation",
        reply="Great, what's the purpose of this NDA?",
    )

    with patch("app.routers.nda.run_chat_turn", return_value=canned_turn):
        response = client.post(
            "/api/nda/chat",
            json={"user_id": user_id, "message": "Acme Inc. and Globex Corporation"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == canned_turn.reply
    assert body["fields"]["partyAName"] == "Acme Inc."
    assert body["fields"]["partyBName"] == "Globex Corporation"

    draft = client.get("/api/nda/draft", params={"user_id": user_id}).json()
    assert draft["fields"]["partyAName"] == "Acme Inc."
    roles = [m["role"] for m in draft["messages"]]
    assert roles == ["assistant", "user", "assistant"]


def test_chat_reuses_same_draft_across_calls(user_id):
    first_turn = NdaChatTurn(party_a_name="Acme Inc.", reply="And the other party?")
    second_turn = NdaChatTurn(
        party_a_name="Acme Inc.",
        party_b_name="Globex Corporation",
        reply="Got it, what's the purpose?",
    )

    with patch("app.routers.nda.run_chat_turn", return_value=first_turn):
        client.post("/api/nda/chat", json={"user_id": user_id, "message": "Acme Inc."})

    with patch("app.routers.nda.run_chat_turn", return_value=second_turn):
        response = client.post(
            "/api/nda/chat",
            json={"user_id": user_id, "message": "Globex Corporation"},
        )

    assert response.status_code == 200
    draft = client.get("/api/nda/draft", params={"user_id": user_id}).json()
    assert draft["fields"]["partyAName"] == "Acme Inc."
    assert draft["fields"]["partyBName"] == "Globex Corporation"
    assert len(draft["messages"]) == 5  # opening + 2 user + 2 assistant
