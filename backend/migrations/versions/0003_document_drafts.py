"""replace nda_drafts/nda_draft_messages with generic document_drafts

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("nda_draft_messages")
    op.drop_table("nda_drafts")

    op.create_table(
        "document_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("document_type", sa.String(length=64), nullable=True),
        sa.Column(
            "fields",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "document_draft_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "draft_id",
            sa.Integer(),
            sa.ForeignKey("document_drafts.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_document_draft_messages_draft_id", "document_draft_messages", ["draft_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_draft_messages_draft_id", table_name="document_draft_messages"
    )
    op.drop_table("document_draft_messages")
    op.drop_table("document_drafts")

    op.create_table(
        "nda_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("party_a_name", sa.Text(), nullable=True),
        sa.Column("party_b_name", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("mnda_term", sa.Text(), nullable=True),
        sa.Column("term_of_confidentiality", sa.Text(), nullable=True),
        sa.Column("governing_law", sa.Text(), nullable=True),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "nda_draft_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "draft_id",
            sa.Integer(),
            sa.ForeignKey("nda_drafts.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_nda_draft_messages_draft_id", "nda_draft_messages", ["draft_id"]
    )
