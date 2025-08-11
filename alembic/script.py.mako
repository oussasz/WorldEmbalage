"""Generic Alembic revision script."""
from __future__ import annotations
revision = '${up_revision}'
down_revision = ${down_revision | repr}
branch_labels = ${branch_labels | repr}
depends_on = ${depends_on | repr}

from alembic import op
import sqlalchemy as sa


def upgrade():
    ${upgrades if upgrades else 'pass'}


def downgrade():
    ${downgrades if downgrades else 'pass'}
