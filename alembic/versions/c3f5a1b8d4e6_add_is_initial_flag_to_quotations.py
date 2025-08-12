"""Add is_initial flag to quotations

Revision ID: c3f5a1b8d4e6
Revises: b2a8c4d6e123
Create Date: 2025-08-12 15:00:00.000000

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3f5a1b8d4e6'
down_revision = 'b2a8c4d6e123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_initial column to quotations table
    with op.batch_alter_table('quotations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_initial', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove is_initial column from quotations table
    with op.batch_alter_table('quotations', schema=None) as batch_op:
        batch_op.drop_column('is_initial')
