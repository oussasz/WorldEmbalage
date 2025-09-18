"""Generic Alembic revision script."""
from __future__ import annotations
revision = 'f0eedd4c5ddd'
down_revision = 'f9a2b8c3d4e5'
branch_labels = 'None'
depends_on = 'None'

from alembic import op
import sqlalchemy as sa


def upgrade():
    pass


def downgrade():
    pass
