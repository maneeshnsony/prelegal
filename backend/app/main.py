from fastapi import FastAPI

app = FastAPI(title="Prelegal API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
