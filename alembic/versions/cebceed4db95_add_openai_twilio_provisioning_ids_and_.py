"""Add OpenAI & Twilio provisioning IDs and timestamps to clients

Revision ID: cebceed4db95
Revises: 
Create Date: 2025-12-29
"""
from alembic import op
import sqlalchemy as sa

revision = "cebceed4db95"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    existing = {row[0] for row in conn.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='clients'")
    )}

    if "twilio_flow_sid" not in existing:
        op.add_column('clients', sa.Column('twilio_flow_sid', sa.String(), nullable=True))

    if "assistant_provisioned_at" not in existing:
        op.add_column('clients', sa.Column('assistant_provisioned_at', sa.DateTime(), nullable=True))

    if "twilio_provisioned_at" not in existing:
        op.add_column('clients', sa.Column('twilio_provisioned_at', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('clients', 'twilio_flow_sid')
    op.drop_column('clients', 'assistant_provisioned_at')
    op.drop_column('clients', 'twilio_provisioned_at')
