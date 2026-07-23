from sqlalchemy import func, select
from sqlalchemy.engine import Connection

from fastapi import APIRouter

from app.db import engine
from app.llm import nda_chat_turn_to_form_data, run_chat_turn
from app.models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DraftResponse,
    NdaFormData,
    nda_draft_messages,
    nda_drafts,
)

router = APIRouter(prefix="/api/nda", tags=["nda"])

OPENING_MESSAGE = (
    "Hi! I'll help you put together a Mutual NDA. To start, who are the two "
    "parties entering into this agreement?"
)

DRAFT_FIELD_COLUMNS = [
    "party_a_name",
    "party_b_name",
    "effective_date",
    "purpose",
    "mnda_term",
    "term_of_confidentiality",
    "governing_law",
    "jurisdiction",
]


def _draft_row_to_form_data(draft_row) -> NdaFormData:
    return NdaFormData(
        partyAName=draft_row.party_a_name or "",
        partyBName=draft_row.party_b_name or "",
        effectiveDate=draft_row.effective_date or "",
        purpose=draft_row.purpose or "",
        mndaTerm=draft_row.mnda_term or "",
        termOfConfidentiality=draft_row.term_of_confidentiality or "",
        governingLaw=draft_row.governing_law or "",
        jurisdiction=draft_row.jurisdiction or "",
    )


def _get_or_create_draft(conn: Connection, user_id: int):
    draft_row = conn.execute(
        select(nda_drafts).where(nda_drafts.c.user_id == user_id)
    ).first()
    if draft_row is not None:
        return draft_row

    draft_id = conn.execute(
        nda_drafts.insert().values(user_id=user_id).returning(nda_drafts.c.id)
    ).scalar_one()
    conn.execute(
        nda_draft_messages.insert().values(
            draft_id=draft_id, role="assistant", content=OPENING_MESSAGE
        )
    )
    return conn.execute(
        select(nda_drafts).where(nda_drafts.c.id == draft_id)
    ).first()


def _load_messages(conn: Connection, draft_id: int) -> list[ChatMessage]:
    rows = conn.execute(
        select(nda_draft_messages.c.role, nda_draft_messages.c.content)
        .where(nda_draft_messages.c.draft_id == draft_id)
        .order_by(nda_draft_messages.c.id)
    ).all()
    return [ChatMessage(role=row.role, content=row.content) for row in rows]


@router.get("/draft")
def get_draft(user_id: int) -> DraftResponse:
    with engine.begin() as conn:
        draft_row = _get_or_create_draft(conn, user_id)
        messages = _load_messages(conn, draft_row.id)

    return DraftResponse(fields=_draft_row_to_form_data(draft_row), messages=messages)


@router.post("/chat")
def chat(payload: ChatRequest) -> ChatResponse:
    with engine.begin() as conn:
        draft_row = _get_or_create_draft(conn, payload.user_id)
        history = _load_messages(conn, draft_row.id)
        current_fields = _draft_row_to_form_data(draft_row)

        turn = run_chat_turn(history, current_fields, payload.message)

        conn.execute(
            nda_draft_messages.insert().values(
                draft_id=draft_row.id, role="user", content=payload.message
            )
        )
        conn.execute(
            nda_draft_messages.insert().values(
                draft_id=draft_row.id, role="assistant", content=turn.reply
            )
        )
        conn.execute(
            nda_drafts.update()
            .where(nda_drafts.c.id == draft_row.id)
            .values(
                party_a_name=turn.party_a_name,
                party_b_name=turn.party_b_name,
                effective_date=turn.effective_date,
                purpose=turn.purpose,
                mnda_term=turn.mnda_term,
                term_of_confidentiality=turn.term_of_confidentiality,
                governing_law=turn.governing_law,
                jurisdiction=turn.jurisdiction,
                updated_at=func.now(),
            )
        )

    return ChatResponse(reply=turn.reply, fields=nda_chat_turn_to_form_data(turn))
