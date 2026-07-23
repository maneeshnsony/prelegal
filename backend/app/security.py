import os
import time
from pathlib import Path

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 60 * 60 * 24 * 7


def _secret_key() -> str:
    return os.environ["SESSION_SECRET_KEY"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, email: str) -> str:
    payload = {"sub": str(user_id), "email": email, "exp": int(time.time()) + JWT_EXPIRY_SECONDS}
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, _secret_key(), algorithms=[JWT_ALGORITHM])
