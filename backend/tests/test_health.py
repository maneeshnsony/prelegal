from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


from unittest.mock import patch


def test_startup_calls_ensure_database_and_migrations():
    with patch("app.main.ensure_database_exists") as mock_ensure, patch(
        "app.main.subprocess.run"
    ) as mock_run:
        with TestClient(app) as startup_client:
            response = startup_client.get("/api/health")
            assert response.status_code == 200
    mock_ensure.assert_called_once()
    mock_run.assert_called_once()
