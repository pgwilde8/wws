from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('clients', sa.Column('assistant_provisioned_at', sa.DateTime(), nullable=True))
    op.add_column('clients', sa.Column('twilio_provisioned_at', sa.DateTime(), nullable=True))
    op.add_column('clients', sa.Column('phone_fallback', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('clients', 'assistant_provisioned_at')
    op.drop_column('clients', 'twilio_provisioned_at')
    op.drop_column('clients', 'phone_fallback')
