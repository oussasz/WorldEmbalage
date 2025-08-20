"""Add partial delivery tracking for raw materials

Revision ID: e8f3c7d2a1b9
Revises: 4b16c504a3d1
Create Date: 2025-08-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'e8f3c7d2a1b9'
down_revision = '4b16c504a3d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create material_deliveries table for tracking partial deliveries
    op.create_table('material_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_order_line_item_id', sa.Integer(), nullable=False),
        sa.Column('delivery_date', sa.Date(), server_default=sa.text('(CURRENT_DATE)'), nullable=False),
        sa.Column('received_quantity', sa.Integer(), nullable=False),
        sa.Column('batch_reference', sa.String(length=64), nullable=True),
        sa.Column('quality_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_order_line_item_id'], ['supplier_order_line_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CreateIndex('ix_material_deliveries_supplier_order_line_item_id', ['supplier_order_line_item_id']),
        sa.CreateIndex('ix_material_deliveries_delivery_date', ['delivery_date'])
    )
    
    # Add delivery status and tracking fields to supplier_order_line_items
    op.add_column('supplier_order_line_items', sa.Column('total_received_quantity', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('supplier_order_line_items', sa.Column('delivery_status', sa.String(length=20), nullable=False, server_default="'pending'"))
    
    # Add index for delivery status
    op.create_index('ix_supplier_order_line_items_delivery_status', 'supplier_order_line_items', ['delivery_status'])


def downgrade() -> None:
    # Remove added columns
    op.drop_index('ix_supplier_order_line_items_delivery_status', table_name='supplier_order_line_items')
    op.drop_column('supplier_order_line_items', 'delivery_status')
    op.drop_column('supplier_order_line_items', 'total_received_quantity')
    
    # Drop material_deliveries table
    op.drop_table('material_deliveries')
