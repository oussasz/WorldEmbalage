"""Add business registration fields to clients table

Revision ID: f9a2b8c3d4e5
Revises: e8f3c7d2a1b9
Create Date: 2025-09-09 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f9a2b8c3d4e5'
down_revision = 'e8f3c7d2a1b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add optional business registration fields to clients table
    op.add_column('clients', sa.Column('numero_rc', sa.String(length=50), nullable=True))
    op.add_column('clients', sa.Column('nis', sa.String(length=50), nullable=True))
    op.add_column('clients', sa.Column('nif', sa.String(length=50), nullable=True))
    op.add_column('clients', sa.Column('ai', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove the business registration fields
    op.drop_column('clients', 'ai')
    op.drop_column('clients', 'nif')
    op.drop_column('clients', 'nis')
    op.drop_column('clients', 'numero_rc')
