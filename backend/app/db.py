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


def reset_database() -> None:
    target = os.environ["DB_DATABASE"]
    maintenance_engine = get_engine("postgres")
    with maintenance_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{target}"'))
        conn.execute(text(f'CREATE DATABASE "{target}"'))
    maintenance_engine.dispose()


engine = get_engine()
