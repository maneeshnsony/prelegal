import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

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


frontend_dist_dir = Path(
    os.environ.get("FRONTEND_DIST_DIR", Path(__file__).resolve().parents[2] / "frontend" / "out")
)

if frontend_dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
