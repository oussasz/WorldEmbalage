"""update_supplier_order_status_to_three_values

Revision ID: 4b16c504a3d1
Revises: c3f5a1b8d4e6
Create Date: 2025-08-13

"""
from __future__ import annotations
revision = '4b16c504a3d1'
down_revision = 'c3f5a1b8d4e6'
branch_labels = 'None'
depends_on = 'None'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # For SQLite, we need to handle enum changes differently
    # SQLite stores enums as text, so we just need to update the values
    
    # Update existing records to use new values
    # Map old values to new ones:
    connection = op.get_bind()
    
    # Update old status values to new 3-status system
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'commande_initial' WHERE status IN ('commandé', 'pending', 'confirmed')"))
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'commande_passee' WHERE status = 'en_transit'"))
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'commande_arrivee' WHERE status IN ('en_stock', 'fermé')"))


def downgrade():
    # Reverse the migration - map new values back to old ones
    connection = op.get_bind()
    
    # Map new values to old ones for downgrade
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'commandé' WHERE status = 'commande_initial'"))
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'en_transit' WHERE status = 'commande_passee'"))
    connection.execute(sa.text("UPDATE supplier_orders SET status = 'en_stock' WHERE status = 'commande_arrivee'"))
