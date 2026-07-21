import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

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

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        relative_path = full_path.strip("/")

        candidates = [
            frontend_dist_dir / relative_path,
            frontend_dist_dir / f"{relative_path}.html",
            frontend_dist_dir / relative_path / "index.html",
        ] if relative_path else [frontend_dist_dir / "index.html"]

        for candidate in candidates:
            if candidate.is_file():
                return FileResponse(candidate)

        raise HTTPException(status_code=404)
