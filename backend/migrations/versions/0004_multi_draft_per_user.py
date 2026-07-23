"""allow multiple document drafts per user

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-23

"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("document_drafts_user_id_key", "document_drafts", type_="unique")
    op.create_index("ix_document_drafts_user_id", "document_drafts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_document_drafts_user_id", table_name="document_drafts")
    op.create_unique_constraint("document_drafts_user_id_key", "document_drafts", ["user_id"])
