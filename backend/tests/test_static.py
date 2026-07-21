import importlib

from fastapi.testclient import TestClient


def test_serves_static_index_when_dist_dir_present(tmp_path, monkeypatch):
    dist_dir = tmp_path / "out"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<h1>Prelegal</h1>")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist_dir))
    import app.main as main_module

    importlib.reload(main_module)

    client = TestClient(main_module.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Prelegal" in response.text

    # cleanup: reload again without the env var so later tests use defaults
    monkeypatch.delenv("FRONTEND_DIST_DIR", raising=False)
    importlib.reload(main_module)


def test_serves_sibling_html_file_for_extensionless_route(tmp_path, monkeypatch):
    dist_dir = tmp_path / "out"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<h1>Prelegal</h1>")
    (dist_dir / "login.html").write_text("<h1>Sign in</h1>")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist_dir))
    import app.main as main_module

    importlib.reload(main_module)

    client = TestClient(main_module.app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign in" in response.text

    # cleanup: reload again without the env var so later tests use defaults
    monkeypatch.delenv("FRONTEND_DIST_DIR", raising=False)
    importlib.reload(main_module)


def test_rejects_path_traversal_outside_dist_dir(tmp_path, monkeypatch):
    dist_dir = tmp_path / "out"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<h1>Prelegal</h1>")

    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("top secret")

    monkeypatch.setenv("FRONTEND_DIST_DIR", str(dist_dir))
    import app.main as main_module

    importlib.reload(main_module)

    client = TestClient(main_module.app)
    response = client.get("/../secret.txt")
    assert response.status_code == 404

    # cleanup: reload again without the env var so later tests use defaults
    monkeypatch.delenv("FRONTEND_DIST_DIR", raising=False)
    importlib.reload(main_module)
