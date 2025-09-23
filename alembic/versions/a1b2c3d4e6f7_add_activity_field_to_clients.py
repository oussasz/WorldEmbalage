"""Deprecated duplicate migration (no-op). Keep for compatibility.

Revision ID: a1b2c3d4e6f7
Revises: f9a2b8c3d4e5
Create Date: 2025-09-23 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e6f7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:  # pragma: no cover
    pass


def downgrade() -> None:  # pragma: no cover
    pass
