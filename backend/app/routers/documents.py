from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.engine import Connection

from app.db import engine
from app.document_types import DOCUMENT_TYPES, render_document
from app.llm import run_field_turn, run_intake_turn
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DraftResponse,
    RenderedDocument,
    document_draft_messages,
    document_drafts,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _get_or_create_draft(conn: Connection, user_id: int):
    draft_row = conn.execute(
        select(document_drafts).where(document_drafts.c.user_id == user_id)
    ).first()
    if draft_row is not None:
        return draft_row
    draft_id = conn.execute(
        document_drafts.insert().values(user_id=user_id).returning(document_drafts.c.id)
    ).scalar_one()
    return conn.execute(
        select(document_drafts).where(document_drafts.c.id == draft_id)
    ).first()


def _load_messages(conn: Connection, draft_id: int) -> list[ChatMessage]:
    rows = conn.execute(
        select(document_draft_messages.c.role, document_draft_messages.c.content)
        .where(document_draft_messages.c.draft_id == draft_id)
        .order_by(document_draft_messages.c.id)
    ).all()
    return [ChatMessage(role=row.role, content=row.content) for row in rows]


@router.get("/draft")
def get_draft(user_id: int) -> DraftResponse:
    with engine.begin() as conn:
        draft_row = _get_or_create_draft(conn, user_id)
        messages = _load_messages(conn, draft_row.id)
    return DraftResponse(
        document_type=draft_row.document_type, fields=draft_row.fields or {}, messages=messages
    )


@router.post("/chat")
def chat(payload: ChatRequest) -> ChatResponse:
    with engine.begin() as conn:
        draft_row = _get_or_create_draft(conn, payload.user_id)
        history = _load_messages(conn, draft_row.id)

        if draft_row.document_type is None:
            turn = run_intake_turn(history, payload.message)
            document_type = turn.document_type
            new_fields = draft_row.fields or {}
        else:
            turn = run_field_turn(
                draft_row.document_type, history, draft_row.fields or {}, payload.message
            )
            document_type = draft_row.document_type
            new_fields = {**(draft_row.fields or {})}
            for f in DOCUMENT_TYPES[document_type].fields:
                value = getattr(turn, f.field_id)
                if value:
                    new_fields[f.field_id] = value

        conn.execute(
            document_draft_messages.insert().values(
                draft_id=draft_row.id, role="user", content=payload.message
            )
        )
        conn.execute(
            document_draft_messages.insert().values(
                draft_id=draft_row.id, role="assistant", content=turn.reply
            )
        )
        conn.execute(
            document_drafts.update()
            .where(document_drafts.c.id == draft_row.id)
            .values(document_type=document_type, fields=new_fields, updated_at=func.now())
        )

    return ChatResponse(reply=turn.reply, document_type=document_type, fields=new_fields)


@router.get("/draft/render")
def render_draft(user_id: int) -> RenderedDocument:
    with engine.begin() as conn:
        draft_row = _get_or_create_draft(conn, user_id)
    if draft_row.document_type is None:
        raise HTTPException(status_code=409, detail="Document type not chosen yet")
    return render_document(draft_row.document_type, draft_row.fields or {})
