"""
Add missing onboarding columns for single-submit intake.

Revision ID: 202512291210
Revises: cebceed4db95
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa


revision = "202512291210"
down_revision = "cebceed4db95"
branch_labels = None
depends_on = None


def _existing_columns(table_name: str):
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :t
            """
        ),
        {"t": table_name},
    )
    return {r[0] for r in rows}


def upgrade():
    existing = _existing_columns("client_onboarding")

    columns = [
        ("full_name", sa.Column("full_name", sa.String(), nullable=False)),
        ("business_name", sa.Column("business_name", sa.String(), nullable=False)),
        ("industry", sa.Column("industry", sa.String(), nullable=False)),
        ("site_description", sa.Column("site_description", sa.Text(), nullable=False)),
        ("target_audience", sa.Column("target_audience", sa.Text(), nullable=True)),
        ("phone", sa.Column("phone", sa.String(), nullable=True)),
        ("domain_name", sa.Column("domain_name", sa.String(), nullable=False)),
        ("lead_forward_email", sa.Column("lead_forward_email", sa.String(), nullable=False)),
        ("calling_direction", sa.Column("calling_direction", sa.String(), nullable=False, server_default="none")),
        ("wants_sms", sa.Column("wants_sms", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("wants_payments", sa.Column("wants_payments", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("uses_cloudflare", sa.Column("uses_cloudflare", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("cloudflare_email", sa.Column("cloudflare_email", sa.String(), nullable=True)),
        ("twilio_sid", sa.Column("twilio_sid", sa.String(), nullable=True)),
        ("twilio_token", sa.Column("twilio_token", sa.String(), nullable=True)),
        ("twilio_from_number", sa.Column("twilio_from_number", sa.String(), nullable=True)),
        ("stripe_publishable_key", sa.Column("stripe_publishable_key", sa.String(), nullable=True)),
        ("stripe_secret_key", sa.Column("stripe_secret_key", sa.String(), nullable=True)),
        ("has_logo", sa.Column("has_logo", sa.Boolean(), nullable=False, server_default=sa.text("false"))),
        ("brand_colors", sa.Column("brand_colors", sa.String(), nullable=True)),
    ]

    for name, column in columns:
        if name not in existing:
            op.add_column("client_onboarding", column)


def downgrade():
    existing = _existing_columns("client_onboarding")
    for name in [
        "brand_colors",
        "has_logo",
        "stripe_secret_key",
        "stripe_publishable_key",
        "twilio_from_number",
        "twilio_token",
        "twilio_sid",
        "cloudflare_email",
        "uses_cloudflare",
        "wants_payments",
        "wants_sms",
        "calling_direction",
        "lead_forward_email",
        "domain_name",
        "phone",
        "target_audience",
        "site_description",
        "industry",
        "business_name",
        "full_name",
    ]:
        if name in existing:
            op.drop_column("client_onboarding", name)

