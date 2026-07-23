from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user_id
from app.security import create_access_token

app = FastAPI()


@app.get("/whoami")
def whoami(user_id: int = Depends(get_current_user_id)) -> dict:
    return {"user_id": user_id}


client = TestClient(app)


def test_valid_token_resolves_user_id(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-key-thats-long-enough")
    token = create_access_token(user_id=7, email="a@example.com")
    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user_id"] == 7


def test_missing_header_returns_401():
    response = client.get("/whoami")
    assert response.status_code == 401


def test_malformed_header_returns_401():
    response = client.get("/whoami", headers={"Authorization": "not-a-bearer-token"})
    assert response.status_code == 401


def test_invalid_token_returns_401(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-key-thats-long-enough")
    response = client.get("/whoami", headers={"Authorization": "Bearer garbage.token.here"})
    assert response.status_code == 401
