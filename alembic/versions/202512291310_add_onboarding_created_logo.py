"""
Add created_at and logo_url to client_onboarding.

Revision ID: 202512291310
Revises: 202512291210
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa


revision = "202512291310"
down_revision = "202512291210"
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
    existing = _existing_columns("client_onboarding")

    if "created_at" not in existing:
        op.add_column(
            "client_onboarding",
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        )

    if "logo_url" not in existing:
        op.add_column(
            "client_onboarding",
            sa.Column("logo_url", sa.String(), nullable=True),
        )


def downgrade():
    existing = _existing_columns("client_onboarding")

    if "logo_url" in existing:
        op.drop_column("client_onboarding", "logo_url")
    if "created_at" in existing:
        op.drop_column("client_onboarding", "created_at")

