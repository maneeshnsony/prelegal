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
from sqlalchemy.dialects.postgresql import JSONB

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

document_drafts = Table(
    "document_drafts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False, unique=True),
    Column("document_type", String(64), nullable=True),
    Column("fields", JSONB, nullable=False, server_default="{}"),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), server_default=func.now()),
)

document_draft_messages = Table(
    "document_draft_messages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("draft_id", Integer, ForeignKey("document_drafts.id"), nullable=False),
    Column("role", String(20), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class ChatMessage(BaseModel):
    role: str
    content: str


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: int
    email: str
    token: str


class ChatRequest(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    document_type: str | None = None
    fields: dict[str, str] = {}


class DraftResponse(BaseModel):
    document_type: str | None = None
    fields: dict[str, str] = {}
    messages: list[ChatMessage]


class RenderedField(BaseModel):
    field_id: str
    label: str
    value: str


class RenderedParagraph(BaseModel):
    number: int
    title: str
    body: str


class RenderedDocument(BaseModel):
    document_type: str
    title: str
    cover_fields: list[RenderedField]
    paragraphs: list[RenderedParagraph]
    disclaimer: str
