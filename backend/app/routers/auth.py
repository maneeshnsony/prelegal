from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import engine
from app.models import AuthResponse, LoginRequest, SignupRequest, users
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup")
def signup(payload: SignupRequest) -> AuthResponse:
    with engine.begin() as conn:
        existing = conn.execute(select(users.c.id).where(users.c.email == payload.email)).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email already registered")
        try:
            user_id = conn.execute(
                users.insert()
                .values(email=payload.email, password_hash=hash_password(payload.password))
                .returning(users.c.id)
            ).scalar_one()
        except IntegrityError:
            # A concurrent signup for the same email committed between our
            # existence check and this insert; users.email is unique.
            raise HTTPException(status_code=409, detail="Email already registered")
    token = create_access_token(user_id, payload.email)
    return AuthResponse(user_id=user_id, email=payload.email, token=token)


@router.post("/login")
def login(payload: LoginRequest) -> AuthResponse:
    with engine.begin() as conn:
        row = conn.execute(
            select(users.c.id, users.c.email, users.c.password_hash).where(
                users.c.email == payload.email
            )
        ).first()
    if row is None or row.password_hash is None or not verify_password(
        payload.password, row.password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(row.id, row.email)
    return AuthResponse(user_id=row.id, email=row.email, token=token)
