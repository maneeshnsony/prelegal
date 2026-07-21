# PL-9: V1 Technical Foundation — Design

## Goal
Upgrade the frontend-only prototype into the real project skeleton (backend, frontend, database, Docker, start/stop scripts) as described in `CLAUDE.md`, with no product-feature changes. Add a fake login screen (no real authentication) as the entry point.

## Non-goals
- No real authentication (password validation, Google OAuth) — that's a future ticket.
- No changes to the NDA creator's features or templates.
- No AI chat.

## Architecture

```
prelegal/
├── backend/              # FastAPI, uv project
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py       # FastAPI app; mounts static frontend export + API routes
│   │   ├── db.py         # DB engine/session, create-database-if-missing logic
│   │   ├── models.py     # users table (id, email, password_hash, created_at)
│   │   └── migrations/   # Alembic migrations
│   └── tests/
├── frontend/              # existing Next.js app, static-exported
├── scripts/
│   ├── start-mac.sh / stop-mac.sh
│   ├── start-linux.sh / stop-linux.sh
│   └── start-windows.ps1 / stop-windows.ps1
├── Dockerfile              # multi-stage: build frontend static export -> uv/FastAPI image
├── docker-compose.yml      # app + postgres services
└── .env                    # existing; DB creds already present
```

## Frontend
- Add `output: "export"` to `next.config.ts`; build produces `frontend/out/`. Current app has no server-side routes/handlers, so this is a drop-in change.
- Add a `/login` page (email + password inputs, "Sign in" button). Submitting with any values sets a `localStorage` flag (e.g. `prelegal_fake_session`) and redirects to the existing NDA page.
- The NDA page checks for that flag on load and redirects to `/login` if absent. This is a placeholder gate only, not real auth.

## Backend
- FastAPI app serves the static `frontend/out` directory via `StaticFiles`, plus a `/api/health` endpoint to prove the wiring works end-to-end.
- On startup: connects to Postgres, creates the target database if it doesn't already exist (via a maintenance connection to the default `postgres` database), then runs Alembic migrations.
- Migration creates a `users` table: `id` (PK), `email` (unique), `password_hash` (nullable for now), `created_at`. No signup/signin endpoints yet — table exists and is validated via migration, but stays unused until the real auth ticket.

## Docker
- Single multi-stage `Dockerfile`: a Node stage builds the frontend static export; a Python/uv stage runs FastAPI and copies the static files in.
- `docker-compose.yml` defines `app` (backend, port 8000) and `postgres` services.

## Scripts
- `scripts/start-{mac,linux}.sh` and `start-windows.ps1`: `docker compose up -d --build`.
- `scripts/stop-{mac,linux}.sh` and `stop-windows.ps1`: `docker compose down`.

## Testing
- Backend: pytest covering `/api/health`, and a migration test confirming the `users` table is created cleanly against a test Postgres instance.
- Frontend: no new automated tests (no new product logic); manual verification of the full path — start containers, hit `/login`, submit, land on NDA page, generate a PDF — confirms the foundation works end-to-end.

## Open questions / risks
- Static export must be verified compatible with the current Next.js config (no image optimization API, no server actions) — confirm during implementation.
