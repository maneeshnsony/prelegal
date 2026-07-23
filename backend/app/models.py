from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
)

from pydantic import BaseModel

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("password_hash", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

nda_drafts = Table(
    "nda_drafts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False, unique=True),
    Column("party_a_name", Text, nullable=True),
    Column("party_b_name", Text, nullable=True),
    Column("effective_date", Text, nullable=True),
    Column("purpose", Text, nullable=True),
    Column("mnda_term", Text, nullable=True),
    Column("term_of_confidentiality", Text, nullable=True),
    Column("governing_law", Text, nullable=True),
    Column("jurisdiction", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), server_default=func.now()),
)

nda_draft_messages = Table(
    "nda_draft_messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("draft_id", Integer, ForeignKey("nda_drafts.id"), nullable=False),
    Column("role", String(20), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class NdaFormData(BaseModel):
    partyAName: str = ""
    partyBName: str = ""
    effectiveDate: str = ""
    purpose: str = ""
    mndaTerm: str = ""
    termOfConfidentiality: str = ""
    governingLaw: str = ""
    jurisdiction: str = ""


class ChatMessage(BaseModel):
    role: str
    content: str


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    user_id: int
    email: str


class ChatRequest(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    fields: NdaFormData


class DraftResponse(BaseModel):
    fields: NdaFormData
    messages: list[ChatMessage]
