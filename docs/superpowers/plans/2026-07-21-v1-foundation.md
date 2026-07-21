# V1 Technical Foundation (PL-9) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the frontend-only prototype into the real project skeleton — FastAPI backend (uv project), Postgres database with a `users` table, static-exported Next.js frontend served by FastAPI, Docker packaging, and start/stop scripts — with no product-feature changes, plus a fake (non-authenticating) login screen.

**Architecture:** A multi-stage Dockerfile builds the Next.js app as a static export and copies it into a Python/uv image that runs FastAPI. FastAPI serves the static files and one `/api/health` endpoint, and on startup ensures the Postgres database exists and runs an Alembic migration that creates an empty `users` table. The frontend gains a `/login` page; submitting it sets a `localStorage` flag that gates access to the existing NDA page (placeholder only, no real credential checking).

**Tech Stack:** FastAPI, uv, SQLAlchemy 2.x + psycopg3, Alembic, pytest + httpx (backend); Next.js 16 static export (frontend, unchanged libs); Docker + docker-compose; bash/PowerShell scripts.

## Global Constraints

- Backend lives in `backend/`, is a uv project, uses FastAPI. (spec: Architecture)
- Database is Postgres; the app must create the database if it doesn't exist. (spec: Backend)
- `users` table is created via migration now but has no signup/signin endpoints yet — no real auth. (spec: Backend, Non-goals)
- Frontend is statically built and served via FastAPI. (spec: Frontend)
- No changes to NDA creator features or templates. (spec: Non-goals)
- `.env` at repo root already has `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` — use these exact names, don't rename.
- Scripts required: `scripts/start-mac.sh`, `scripts/stop-mac.sh`, `scripts/start-linux.sh`, `scripts/stop-linux.sh`, `scripts/start-windows.ps1`, `scripts/stop-windows.ps1`. (spec: Scripts)
- Backend available at `http://localhost:8000`. (spec: Architecture)

---

### Task 1: Backend project scaffolding + `/api/health`

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.main:app` — a FastAPI instance importable by uvicorn as `app.main:app`, with route `GET /api/health` returning `{"status": "ok"}`.

- [ ] **Step 1: Initialize the uv project**

Run:
```bash
cd backend
uv init --name prelegal-backend --python 3.12 --no-readme --bare
uv add fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" alembic python-dotenv
uv add --dev pytest httpx
```
Expected: `backend/pyproject.toml` and `backend/uv.lock` created with these dependencies listed.

- [ ] **Step 2: Write the failing test**

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

`backend/tests/__init__.py`: empty file.
`backend/app/__init__.py`: empty file.

- [ ] **Step 2b: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.main'` or import error)

- [ ] **Step 3: Write minimal implementation**

`backend/app/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Prelegal API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app backend/tests
git commit -m "Scaffold FastAPI backend with health endpoint"
```

---

### Task 2: Database connection + create-database-if-missing

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/tests/test_db.py`
- Modify: `backend/pyproject.toml` (no change needed — deps already added in Task 1)

**Interfaces:**
- Consumes: `.env` values `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` (repo root `.env`, loaded via `python-dotenv`).
- Produces: `app.db.ensure_database_exists() -> None`, `app.db.get_engine(database: str | None = None) -> sqlalchemy.engine.Engine`, `app.db.engine` (module-level `Engine` bound to `DB_DATABASE`).

- [ ] **Step 1: Write the failing test**

`backend/tests/test_db.py`:
```python
import os
import uuid

import pytest
from sqlalchemy import inspect, text

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
        with get_engine("postgres").connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_db.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.db'`)

- [ ] **Step 3: Write minimal implementation**

`backend/app/db.py`:
```python
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _url(database: str) -> str:
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    user = os.environ["DB_USERNAME"]
    password = os.environ["DB_PASSWORD"]
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def get_engine(database: str | None = None) -> Engine:
    target = database or os.environ["DB_DATABASE"]
    return create_engine(_url(target))


def ensure_database_exists() -> None:
    target = os.environ["DB_DATABASE"]
    maintenance_engine = get_engine("postgres")
    with maintenance_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": target},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{target}"'))
    maintenance_engine.dispose()


engine = get_engine()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_db.py -v`
Expected: PASS if Postgres is reachable via `.env` values, otherwise SKIPPED (not FAIL).

- [ ] **Step 5: Commit**

```bash
git add backend/app/db.py backend/tests/test_db.py
git commit -m "Add Postgres connection with create-database-if-missing"
```

---

### Task 3: Alembic migration for `users` table

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/0001_create_users_table.py`
- Create: `backend/tests/test_migrations.py`

**Interfaces:**
- Consumes: `app.db.ensure_database_exists`, `app.db._url` (via `DB_*` env vars) for Alembic's `env.py` to build its own engine URL.
- Produces: a `users` table (columns: `id` PK serial, `email` unique not-null, `password_hash` nullable text, `created_at` timestamptz not-null default now) reachable after `alembic upgrade head`.

- [ ] **Step 1: Initialize Alembic**

Run:
```bash
cd backend
uv run alembic init migrations
```
Expected: creates `backend/alembic.ini` and `backend/migrations/` with `env.py`, `script.py.mako`, `versions/`.

- [ ] **Step 2: Point Alembic at the project database URL**

Edit `backend/migrations/env.py`, replacing the `config.get_main_option("sqlalchemy.url")` usage near the top of `run_migrations_online`/`run_migrations_offline` (or wherever `target_metadata`/URL is set) with:
```python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import _url  # noqa: E402

config.set_main_option("sqlalchemy.url", _url(os.environ["DB_DATABASE"]))
```
Add this block immediately after the existing `config = context.config` line, before `target_metadata = None`. Leave `target_metadata = None` (no ORM models to autogenerate from — this migration is written by hand).

- [ ] **Step 3: Write the failing test**

`backend/tests/test_migrations.py`:
```python
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import inspect

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


def test_migration_creates_users_table(monkeypatch):
    test_db_name = f"prelegal_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("DB_DATABASE", test_db_name)
    ensure_database_exists()
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd="backend" if __name__ == "__main__" else ".",
            check=True,
        )
        inspector = inspect(get_engine(test_db_name))
        columns = {col["name"] for col in inspector.get_columns("users")}
        assert columns == {"id", "email", "password_hash", "created_at"}
    finally:
        with get_engine("postgres").connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            from sqlalchemy import text

            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}"'))
```

Note: run this test from the `backend/` directory (`cd backend && uv run pytest tests/test_migrations.py -v`) so the relative `alembic upgrade head` call resolves `alembic.ini` correctly; simplify the `cwd=` argument above to `"."` since pytest is already invoked from `backend/`.

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_migrations.py -v`
Expected: FAIL (no `versions/0001_create_users_table.py` yet, so `users` table doesn't exist / upgrade is a no-op)

- [ ] **Step 5: Write the migration**

Run: `cd backend && uv run alembic revision -m "create users table"` and rename the generated file under `backend/migrations/versions/` to `0001_create_users_table.py`, then replace its contents:
```python
"""create users table

Revision ID: 0001
Revises:
Create Date: 2026-07-21
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("users")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_migrations.py -v`
Expected: PASS if Postgres reachable, otherwise SKIPPED.

- [ ] **Step 7: Commit**

```bash
git add backend/alembic.ini backend/migrations backend/tests/test_migrations.py
git commit -m "Add Alembic migration for users table"
```

---

### Task 4: Startup wiring — ensure DB + run migrations before serving

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: `app.db.ensure_database_exists`, subprocess call to `alembic upgrade head`.
- Produces: FastAPI `lifespan` context that runs on app startup (no new public interface beyond existing `/api/health`).

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_health.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: FAIL (`AttributeError`/`AssertionError` — `ensure_database_exists`/`subprocess` not referenced in `app.main` yet)

- [ ] **Step 3: Write minimal implementation**

`backend/app/main.py` (replace full contents):
```python
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import ensure_database_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_exists()
    subprocess.run(["alembic", "upgrade", "head"], cwd="backend", check=True)
    yield


app = FastAPI(title="Prelegal API", lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_health.py
git commit -m "Run database setup and migrations on backend startup"
```

---

### Task 5: Serve the static frontend export from FastAPI

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_static.py`

**Interfaces:**
- Consumes: environment variable `FRONTEND_DIST_DIR` (defaults to `../frontend/out` relative to `backend/`), used only if the directory exists.
- Produces: `GET /` and any non-`/api` path serve `index.html` / matching static file when `FRONTEND_DIST_DIR` exists; API routes remain reachable regardless.

- [ ] **Step 1: Write the failing test**

`backend/tests/test_static.py`:
```python
import importlib
import os

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_static.py -v`
Expected: FAIL (404 — no static mount exists yet)

- [ ] **Step 3: Write minimal implementation**

In `backend/app/main.py`, add after the `/api/health` route definition (keep the `lifespan`/imports from Task 4):
```python
import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles

frontend_dist_dir = Path(
    os.environ.get("FRONTEND_DIST_DIR", Path(__file__).resolve().parents[2] / "frontend" / "out")
)

if frontend_dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
```
This must be the last thing registered in the module (after all `/api/*` routes) so API routes take precedence.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_static.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_static.py
git commit -m "Serve static frontend export from FastAPI"
```

---

### Task 6: Frontend static export configuration

**Files:**
- Modify: `frontend/next.config.ts`
- Modify: `frontend/.gitignore` (ensure `/out` is ignored)

**Interfaces:**
- Produces: `npm run build` in `frontend/` emits a static site into `frontend/out/` (consumed by Task 5's `FRONTEND_DIST_DIR` default and Task 8's Dockerfile).

- [ ] **Step 1: Update Next.js config**

`frontend/next.config.ts`:
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
```

- [ ] **Step 2: Ensure `out/` is gitignored**

Check `frontend/.gitignore` contains a line for `/out`; if not, add it (co-locate with the existing `/.next` ignore entry).

- [ ] **Step 3: Verify the build produces a static export**

Run:
```bash
cd frontend
npm run build
```
Expected: build succeeds, and `frontend/out/index.html` exists (`ls frontend/out/index.html`).

- [ ] **Step 4: Commit**

```bash
git add frontend/next.config.ts frontend/.gitignore
git commit -m "Configure Next.js static export for FastAPI hosting"
```

---

### Task 7: Fake login screen gating the NDA page

**Files:**
- Create: `frontend/src/app/login/page.tsx`
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/lib/fakeSession.ts`

**Interfaces:**
- Produces: `frontend/src/lib/fakeSession.ts` exports `FAKE_SESSION_KEY: string`, `hasFakeSession(): boolean`, `setFakeSession(): void`.
- Consumes (in `page.tsx`): the same `fakeSession` module.

- [ ] **Step 1: Add the fake session helper**

`frontend/src/lib/fakeSession.ts`:
```typescript
export const FAKE_SESSION_KEY = "prelegal_fake_session";

export function hasFakeSession(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(FAKE_SESSION_KEY) === "true";
}

export function setFakeSession(): void {
  window.localStorage.setItem(FAKE_SESSION_KEY, "true");
}
```

- [ ] **Step 2: Add the login page**

`frontend/src/app/login/page.tsx`:
```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { setFakeSession } from "@/lib/fakeSession";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFakeSession();
    router.push("/");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-md border border-gray-200 bg-white p-6"
      >
        <h1 className="mb-4 text-xl font-bold text-gray-900">Sign in</h1>
        <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="mb-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          required
        />
        <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          required
        />
        <button
          type="submit"
          className="w-full rounded-md bg-purple-700 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-800"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}
```
(Uses the project's purple secondary `#753991` — Tailwind's `purple-700`/`purple-800` are close defaults; exact hex alignment is a follow-up styling task, not in scope here.)

- [ ] **Step 3: Gate the NDA page behind the fake session**

Modify `frontend/src/app/page.tsx`: add near the top of the component body (after existing `useState` line, before the `handleDownloadPdf` function):
```tsx
  const router = useRouter();

  useEffect(() => {
    if (!hasFakeSession()) {
      router.replace("/login");
    }
  }, [router]);
```
Add imports at the top of the file:
```tsx
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { hasFakeSession } from "@/lib/fakeSession";
```
(`useState` import from `"react"` becomes `import { useEffect, useState } from "react";`.)

- [ ] **Step 4: Verify manually**

Run:
```bash
cd frontend
npm run dev
```
Visit `http://localhost:3000/` — expect redirect to `/login`. Submit the login form with any values — expect redirect back to `/` showing the NDA creator. Stop the dev server (Ctrl+C) when done.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/login frontend/src/app/page.tsx frontend/src/lib/fakeSession.ts
git commit -m "Add fake login screen gating the NDA creator"
```

---

### Task 8: Docker packaging

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Interfaces:**
- Produces: image built from repo root exposing port 8000; `docker-compose.yml` services `app` (built from `Dockerfile`) and `postgres` (official `postgres:16` image), sharing a network so `app` reaches `postgres` at hostname `postgres`.

- [ ] **Step 1: Write the Dockerfile**

`Dockerfile` (repo root):
```dockerfile
# --- Stage 1: build the static frontend export ---
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: backend runtime ---
FROM python:3.12-slim AS backend
RUN pip install --no-cache-dir uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ ./
COPY --from=frontend-build /app/frontend/out /app/frontend/out
ENV FRONTEND_DIST_DIR=/app/frontend/out
WORKDIR /app
EXPOSE 8000
CMD ["uv", "run", "--project", "backend", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write docker-compose.yml**

`docker-compose.yml` (repo root):
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      DB_HOST: postgres
    depends_on:
      - postgres
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: postgres
    ports:
      - "5432:5432"
    volumes:
      - prelegal_pg_data:/var/lib/postgresql/data

volumes:
  prelegal_pg_data:
```

- [ ] **Step 3: Write .dockerignore**

`.dockerignore` (repo root):
```
frontend/node_modules
frontend/.next
frontend/out
backend/.venv
backend/__pycache__
.git
```

- [ ] **Step 4: Verify the image builds and serves the app**

Run:
```bash
docker compose up -d --build
curl http://localhost:8000/api/health
curl -s http://localhost:8000/ | head -c 200
docker compose down
```
Expected: health check returns `{"status":"ok"}`; root path returns HTML containing the frontend's `index.html` content.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "Add Docker packaging for backend, frontend, and Postgres"
```

---

### Task 9: Start/stop scripts

**Files:**
- Create: `scripts/start-mac.sh`
- Create: `scripts/stop-mac.sh`
- Create: `scripts/start-linux.sh`
- Create: `scripts/stop-linux.sh`
- Create: `scripts/start-windows.ps1`
- Create: `scripts/stop-windows.ps1`

**Interfaces:**
- Produces: each start script runs `docker compose up -d --build` from the repo root; each stop script runs `docker compose down`.

- [ ] **Step 1: Write the mac/linux scripts**

`scripts/start-mac.sh` and `scripts/start-linux.sh` (identical content):
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --build
echo "Prelegal is starting at http://localhost:8000"
```

`scripts/stop-mac.sh` and `scripts/stop-linux.sh` (identical content):
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down
```

- [ ] **Step 2: Make them executable**

Run: `chmod +x scripts/start-mac.sh scripts/stop-mac.sh scripts/start-linux.sh scripts/stop-linux.sh`

- [ ] **Step 3: Write the Windows scripts**

`scripts/start-windows.ps1`:
```powershell
Set-Location (Join-Path $PSScriptRoot "..")
docker compose up -d --build
Write-Host "Prelegal is starting at http://localhost:8000"
```

`scripts/stop-windows.ps1`:
```powershell
Set-Location (Join-Path $PSScriptRoot "..")
docker compose down
```

- [ ] **Step 4: Verify a start/stop cycle**

Run:
```bash
./scripts/start-mac.sh    # or start-linux.sh / start-windows.ps1 depending on OS
curl http://localhost:8000/api/health
./scripts/stop-mac.sh     # or stop-linux.sh / stop-windows.ps1
```
Expected: health check returns `{"status":"ok"}` after start; `docker compose ps` shows no running containers after stop.

- [ ] **Step 5: Commit**

```bash
git add scripts/
git commit -m "Add start/stop scripts for mac, linux, and windows"
```

---

### Task 10: End-to-end manual verification

**Files:** none (verification only)

- [ ] **Step 1: Full stack smoke test**

Run:
```bash
./scripts/start-windows.ps1
```
(or the mac/linux equivalent matching the developer's OS)

- [ ] **Step 2: Walk the golden path**

In a browser, visit `http://localhost:8000/`:
1. Expect redirect to `/login`.
2. Enter any email/password, click "Sign in".
3. Expect redirect to `/` showing the Mutual NDA Creator form.
4. Fill in a few fields and click "Download completed NDA (PDF)".
5. Confirm a PDF downloads with the entered content.

- [ ] **Step 3: Confirm backend health and DB state**

Run:
```bash
curl http://localhost:8000/api/health
docker compose exec postgres psql -U $env:DB_USERNAME -d $env:DB_DATABASE -c "\d users"
```
Expected: health check returns `{"status":"ok"}`; `\d users` shows the `id`, `email`, `password_hash`, `created_at` columns.

- [ ] **Step 4: Stop the stack**

Run:
```bash
./scripts/stop-windows.ps1
```

- [ ] **Step 5: Record results**

No commit needed for this task — if any step fails, file it as a bug and fix in a follow-up task before considering PL-9 done.
