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
COPY catalog.json ./catalog.json
COPY templates/ ./templates/
EXPOSE 8000
CMD ["uv", "run", "--project", "backend", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
