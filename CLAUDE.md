# Prelegal Project

## Overview
This is a SaaS product to allow users to draft legal agreements based on templates in the templates directory. The user AI chat in order to estrablish what document they want and how to fill in the fields. The available documents and conversation catalog.json file in the project root, included here:

@catalog.json

Initial phase (done): a frontend-only prototype that only supports the Mutual NDA document with no AI chat.
Phase 2 (done): V1 technical foundation — real backend, database, Docker packaging, and a fake (non-authenticating) login gate, still with no AI chat and only the Mutual NDA document.
Current phase (done): AI chat intake for the Mutual NDA — a free-form chat (backed by Cerebras/LiteLLM Structured Outputs) replaces the manual field form, still only the Mutual NDA document. See "Implementation Status" at the end of this file.

## Development process
When instructed to build a feature:
1. Use your Atlassian tools to read the feature instructions from Jira
2. Develop the feature - do not skip any step from the feature-dev 7 step process
3. Thoroughly test the feature with unit tests and integration tests and fix any issues
4. Submit a PR using your github tools

## AI design
When writing code to make calls to LLMs, use your Cerebras skill to use LiteLLM via OpenRouter to the gpt-oss-120b model with Cerebras as the inference provider. You should use Structured Outputs so that you can interpret the results and populate fields in the legal document.

There is an OPENROUTER_API_KEY in the .env file in the project root.

## Technical design
The entire project should be packaged into a Docker container.
The backend should be in backend/ and be a uv project, using FastAPI.
The database should use postgres and create database if doesn't exist. Allow the users table with singup and sing in. Google oAuth also be allowed. Postgres db credentials are in .env file.
The frontend should be in frontend/
The frontend is statically built and served via FastAPI (Next.js static export mounted from the backend).
There should be scripts in scripts/ for:
```bash
# Mac
scripts/start-mac.sh    # Start
scripts/stop-mac.sh     # Stop

# Linux
scripts/start-linux.sh    # Start
scripts/stop-linux.sh     # Stop

# Windows
scripts/start-windows.ps1    # Start
scripts/stop-windows.ps1     # Stop
```

Backend available at http://localhost:8000

## Color Scheme
- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991` (submit buttons)
- Dark Navy: `#032147` (headings)
- Gray Text: `#888888`

## Implementation Status

**PL-9 — V1 technical foundation (done, merged to main):**
- Backend: FastAPI app in `backend/` (uv project) with `GET /api/health`. Runs on `http://localhost:8000`.
- Database: Postgres connection via SQLAlchemy/psycopg in `backend/app/db.py`, creates the database on startup if missing. Alembic migration creates an empty `users` table (`id`, `email`, `password_hash`, `created_at`) — no signup/signin endpoints or Google OAuth yet, no real auth.
- Frontend: Next.js static export (`frontend/next.config.ts` → `output: "export"`) served by FastAPI via `StaticFiles`, mounted from `backend/app/main.py`.
- Login: `/login` is a fake, non-authenticating page — submitting any credentials sets a `localStorage` flag (`frontend/src/lib/fakeSession.ts`) that gates access to the NDA creator. No real credential checking yet.
- Docker: multi-stage root `Dockerfile` (frontend build → backend runtime) plus `docker-compose.yml` (`app` + `postgres` services).
- Scripts: `scripts/start-{mac,linux}.sh`, `scripts/stop-{mac,linux}.sh`, `scripts/start-windows.ps1`, `scripts/stop-windows.ps1` — all wrap `docker compose up -d --build` / `docker compose down`.

**PL-10 — AI chat intake for the Mutual NDA (done, merged to main):**
- Database: two new tables via `backend/migrations/versions/0002_create_nda_chat_tables.py` — `nda_drafts` (one row per user, the 8 NDA fields as discrete text columns, FK to `users.id`) and `nda_draft_messages` (chat history, FK to `nda_drafts.id`). Both were later replaced by PL-11's generic tables (see below).
- Backend: `backend/app/models.py` (Core table defs + Pydantic schemas), `backend/app/llm.py` (`NdaChatTurn` Structured Output model, system prompt builder, `run_chat_turn` calling `litellm.completion` with `openrouter/openai/gpt-oss-120b` via Cerebras), `backend/app/routers/auth.py` (`POST /api/auth/login` — creates/finds a `users` row by email, still no password check) and `backend/app/routers/nda.py` (`POST /api/nda/chat`, `GET /api/nda/draft`).
- Frontend: `frontend/src/lib/fakeSession.ts` now stores a real `user_id` (returned by `/api/auth/login`) instead of a boolean flag; `frontend/src/lib/api.ts` is the fetch wrapper for the new endpoints; `frontend/src/components/NdaChat.tsx` (chat UI) replaces the deleted `NdaForm.tsx`; `frontend/src/app/page.tsx` hydrates from `GET /api/nda/draft`, drives the conversation, and gates the existing PDF/txt download buttons on all 8 fields being non-empty (checked client-side).
- Login (`/login`) still doesn't verify a password — it now calls the backend to create-or-find a `users` row and stores the returned id, but any password value is accepted.
- Tests: `backend/tests/test_auth.py`, `test_llm.py`, `test_nda_chat.py` (mocked LLM calls + real/skippable-Postgres integration tests). Frontend has no test runner configured; verified manually via `next build`/`tsc --noEmit` and a live `docker compose` smoke test.

**PL-11 — Expand to all 11 catalog document types (done, merged to main):**
- Backend: `backend/app/document_types.py` parses each `templates/*.md` file for `<span class="..._link">Label</span>` markers at import time to derive a per-document field schema (`DOCUMENT_TYPES`), with one JSON sidecar (`backend/app/document_type_overrides.json`) covering the Mutual NDA's cover-page-only party names — no per-document Python/TypeScript code needed to add a template. Dynamic Pydantic models are built per document type with `pydantic.create_model()` (`build_field_turn_model`, `lru_cache`d) and rendering (substituting field values back into template text) happens server-side via `render_document`.
- AI chat is now two-mode: an intake turn (`IntakeTurn`, `run_intake_turn` in `backend/app/llm.py`) that picks which of the 11 document types the user wants — or, for an unsupported request, proposes the closest available match via `suggested_document_type` without committing — followed by a generalized field-filling turn (`run_field_turn`) once a document type is set.
- Database: the NDA-only `nda_drafts`/`nda_draft_messages` tables were dropped and replaced (migration `backend/migrations/versions/0003_document_drafts.py`) with generic `document_drafts` (`document_type` + a `fields` JSONB map) and `document_draft_messages` tables.
- Routes: `backend/app/routers/nda.py` was replaced by `backend/app/routers/documents.py` (`GET /api/documents/draft`, `POST /api/documents/chat`, `GET /api/documents/draft/render`) — later re-scoped per-draft in PL-12.
- Frontend: `frontend/src/lib/documentTypes.ts` plus a generalized `api.ts`; `NdaChat.tsx`/`NdaDocument.tsx` were replaced by `DocumentChat.tsx`/`DocumentPreview.tsx`, and `ndaTemplate.ts`/`ndaPdf.ts` by a generic `documentPdf.ts`, all driven by the document type returned from the backend rather than hardcoded NDA fields.

**PL-12 — Real authentication, multi-document history, and SaaS polish (done, merged to main):**
- Auth: `backend/app/security.py` (bcrypt password hashing, JWT creation/decoding with a `SESSION_SECRET_KEY`) and `backend/app/deps.py` (`get_current_user_id` FastAPI dependency reading the `Authorization: Bearer` header) replace the old fake email-only login. `backend/app/routers/auth.py` now exposes `POST /api/auth/signup` and `POST /api/auth/login`, both password-verified, returning a JWT. Google OAuth is confirmed still not implemented — `auth.py` only handles email/password.
- Multi-draft: migration `backend/migrations/versions/0004_multi_draft_per_user.py` drops the one-draft-per-user uniqueness constraint on `document_drafts.user_id`. `backend/app/routers/documents.py` routes are now token-scoped (user id comes from the JWT, never a client-supplied param) and draft-scoped: `GET /api/documents` (list, newest first), `POST /api/documents` (create), `GET /api/documents/{draft_id}`, `POST /api/documents/{draft_id}/chat`, `GET /api/documents/{draft_id}/render` — each 404s if the draft isn't owned by the caller.
- Database lifecycle: `backend/app/db.py` gained `reset_database()`, called from the FastAPI `lifespan` in `backend/app/main.py` on every startup — the database is dropped and recreated (then migrated) each time the backend restarts, a deliberate simplification; no persistent storage across restarts yet.
- Disclaimer: a fixed `DISCLAIMER_TEXT` constant in `backend/app/document_types.py` is returned as `RenderedDocument.disclaimer` on every render response, and shown identically on-screen, in PDF exports, and in text exports on the frontend.
- Frontend: `frontend/src/lib/fakeSession.ts` was replaced by `frontend/src/lib/session.ts` (real JWT storage) and a token-authenticated `api.ts`. New screens: `frontend/src/app/signup/page.tsx`, `frontend/src/app/documents/page.tsx` ("My Documents" list with completion badges), `frontend/src/app/documents/view/page.tsx` (per-draft chat/creator view, `?id=`-based since static export can't pre-render dynamic segments); the root `frontend/src/app/page.tsx` is now just an auth-gated redirect to `/documents` or `/login`. A shared `frontend/src/components/AppShell.tsx` (nav, signed-in email, sign-out) and `frontend/src/components/DisclaimerBanner.tsx` wrap all authenticated screens, styled with the CLAUDE.md brand palette.

**Not yet built:** Google OAuth (confirmed absent in `backend/app/routers/auth.py`); persistent/non-resetting database storage (the database is intentionally dropped and recreated on every backend startup, so accounts and documents don't survive a restart); email verification, password reset, or "remember me"/refresh-token session flows.