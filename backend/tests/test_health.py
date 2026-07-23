from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


from unittest.mock import patch


def test_startup_calls_reset_database_and_migrations():
    with patch("app.main.reset_database") as mock_reset, patch(
        "app.main.subprocess.run"
    ) as mock_run:
        with TestClient(app) as startup_client:
            response = startup_client.get("/api/health")
            assert response.status_code == 200
    mock_reset.assert_called_once()
    mock_run.assert_called_once()
