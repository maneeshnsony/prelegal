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
