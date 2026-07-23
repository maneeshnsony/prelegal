from fastapi import APIRouter
from sqlalchemy import select

from app.db import engine
from app.models import LoginRequest, LoginResponse, users

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest) -> LoginResponse:
    with engine.begin() as conn:
        row = conn.execute(
            select(users.c.id, users.c.email).where(users.c.email == payload.email)
        ).first()
        if row is None:
            result = conn.execute(
                users.insert().values(email=payload.email).returning(users.c.id)
            )
            user_id = result.scalar_one()
        else:
            user_id = row.id

    return LoginResponse(user_id=user_id, email=payload.email)
