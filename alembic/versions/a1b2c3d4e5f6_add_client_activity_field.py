"""Add client activity field to clients table

Revision ID: a1b2c3d4e5f6
Revises: f9a2b8c3d4e5
Create Date: 2025-09-23 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f0eedd4c5ddd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add optional 'activity' field to clients
    op.add_column('clients', sa.Column('activity', sa.String(length=128), nullable=True))


def downgrade() -> None:
    # Remove the 'activity' field
    op.drop_column('clients', 'activity')
