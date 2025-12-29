"""
Add assistant_status_detail and twilio_status_detail to clients.

Revision ID: 202512291400
Revises: 202512291310
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa


revision = "202512291400"
down_revision = "202512291310"
branch_labels = None
depends_on = None


def _existing_columns(table: str):
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :t
            """
        ),
        {"t": table},
    )
    return {r[0] for r in rows}


def upgrade():
    existing = _existing_columns("clients")
    if "assistant_status_detail" not in existing:
        op.add_column("clients", sa.Column("assistant_status_detail", sa.Text(), nullable=True))
    if "twilio_status_detail" not in existing:
        op.add_column("clients", sa.Column("twilio_status_detail", sa.Text(), nullable=True))


def downgrade():
    existing = _existing_columns("clients")
    if "twilio_status_detail" in existing:
        op.drop_column("clients", "twilio_status_detail")
    if "assistant_status_detail" in existing:
        op.drop_column("clients", "assistant_status_detail")

