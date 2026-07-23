from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.engine import Connection

from app.db import engine
from app.deps import get_current_user_id
from app.document_types import DOCUMENT_TYPES, render_document
from app.llm import run_field_turn, run_intake_turn
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DraftResponse,
    DraftSummary,
    RenderedDocument,
    document_draft_messages,
    document_drafts,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _is_complete(document_type: str | None, fields: dict) -> bool:
    if document_type is None:
        return False
    return all(fields.get(f.field_id, "").strip() for f in DOCUMENT_TYPES[document_type].fields)


def _get_owned_draft(conn: Connection, draft_id: int, user_id: int):
    draft_row = conn.execute(
        select(document_drafts).where(
            document_drafts.c.id == draft_id, document_drafts.c.user_id == user_id
        )
    ).first()
    if draft_row is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return draft_row


def _load_messages(conn: Connection, draft_id: int) -> list[ChatMessage]:
    rows = conn.execute(
        select(document_draft_messages.c.role, document_draft_messages.c.content)
        .where(document_draft_messages.c.draft_id == draft_id)
        .order_by(document_draft_messages.c.id)
    ).all()
    return [ChatMessage(role=row.role, content=row.content) for row in rows]


@router.get("")
def list_drafts(user_id: int = Depends(get_current_user_id)) -> list[DraftSummary]:
    with engine.begin() as conn:
        rows = conn.execute(
            select(document_drafts)
            .where(document_drafts.c.user_id == user_id)
            .order_by(document_drafts.c.updated_at.desc())
        ).all()
    return [
        DraftSummary(
            id=row.id,
            document_type=row.document_type,
            title=DOCUMENT_TYPES[row.document_type].title
            if row.document_type
            else "Untitled document",
            updated_at=row.updated_at,
            is_complete=_is_complete(row.document_type, row.fields or {}),
        )
        for row in rows
    ]


@router.post("")
def create_draft(user_id: int = Depends(get_current_user_id)) -> DraftResponse:
    with engine.begin() as conn:
        draft_id = conn.execute(
            document_drafts.insert().values(user_id=user_id).returning(document_drafts.c.id)
        ).scalar_one()
    return DraftResponse(id=draft_id, document_type=None, fields={}, messages=[])


@router.get("/{draft_id}")
def get_draft(draft_id: int, user_id: int = Depends(get_current_user_id)) -> DraftResponse:
    with engine.begin() as conn:
        draft_row = _get_owned_draft(conn, draft_id, user_id)
        messages = _load_messages(conn, draft_row.id)
    return DraftResponse(
        id=draft_row.id,
        document_type=draft_row.document_type,
        fields=draft_row.fields or {},
        messages=messages,
    )


@router.post("/{draft_id}/chat")
def chat(
    draft_id: int, payload: ChatRequest, user_id: int = Depends(get_current_user_id)
) -> ChatResponse:
    with engine.begin() as conn:
        draft_row = _get_owned_draft(conn, draft_id, user_id)
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


@router.get("/{draft_id}/render")
def render_draft(draft_id: int, user_id: int = Depends(get_current_user_id)) -> RenderedDocument:
    with engine.begin() as conn:
        draft_row = _get_owned_draft(conn, draft_id, user_id)
    if draft_row.document_type is None:
        raise HTTPException(status_code=409, detail="Document type not chosen yet")
    return render_document(draft_row.document_type, draft_row.fields or {})
