"""Update quantity columns to string for estimated quantities

Revision ID: b2a8c4d6e123
Revises: d7b149c98edd
Create Date: 2025-08-12 12:00:00.000000

"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2a8c4d6e123'
down_revision = 'd7b149c98edd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update quantity column in quotation_line_items to String
    with op.batch_alter_table('quotation_line_items', schema=None) as batch_op:
        batch_op.alter_column('quantity', 
                              existing_type=sa.Integer(),
                              type_=sa.String(100),
                              existing_nullable=False,
                              nullable=False)
    
    # Update quantity column in client_order_line_items to String  
    with op.batch_alter_table('client_order_line_items', schema=None) as batch_op:
        batch_op.alter_column('quantity',
                              existing_type=sa.Integer(), 
                              type_=sa.String(100),
                              existing_nullable=False,
                              nullable=False)


def downgrade() -> None:
    # Revert quantity column in client_order_line_items back to Integer
    with op.batch_alter_table('client_order_line_items', schema=None) as batch_op:
        batch_op.alter_column('quantity',
                              existing_type=sa.String(100),
                              type_=sa.Integer(),
                              existing_nullable=False,
                              nullable=False)
    
    # Revert quantity column in quotation_line_items back to Integer
    with op.batch_alter_table('quotation_line_items', schema=None) as batch_op:
        batch_op.alter_column('quantity',
                              existing_type=sa.String(100), 
                              type_=sa.Integer(),
                              existing_nullable=False,
                              nullable=False)
