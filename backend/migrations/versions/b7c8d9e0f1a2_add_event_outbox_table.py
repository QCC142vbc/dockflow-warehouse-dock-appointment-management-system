"""add event_outbox table

Revision ID: b7c8d9e0f1a2
Revises: f3a1b2c4d5e6
Create Date: 2026-10-31 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'f3a1b2c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'event_outbox',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_version', sa.String(length=20), server_default='1.0', nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_outbox_event_id'), 'event_outbox', ['event_id'], unique=True)
    op.create_index(op.f('ix_event_outbox_event_type'), 'event_outbox', ['event_type'], unique=False)
    op.create_index(op.f('ix_event_outbox_status'), 'event_outbox', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_event_outbox_status'), table_name='event_outbox')
    op.drop_index(op.f('ix_event_outbox_event_type'), table_name='event_outbox')
    op.drop_index(op.f('ix_event_outbox_event_id'), table_name='event_outbox')
    op.drop_table('event_outbox')
