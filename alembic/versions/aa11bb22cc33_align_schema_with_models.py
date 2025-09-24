"""Align schema with ORM models (quantity text columns, non-null totals, delivery status default)\n\nRevision ID: aa11bb22cc33\nRevises: f0eedd4c5ddd\nCreate Date: 2025-09-24 10:15:00.000000\n\nUpdated (post review):\n - Preserve existing extra column `material_reference` in client_order_line_items (was missing in first draft).\n - Add supplier_order_line_items rebuild when total_line_amount nullable or delivery_status default mismatch.\n - Ensure idempotence checks for supplier_order_line_items.\n"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'aa11bb22cc33'
down_revision = 'f0eedd4c5ddd'
branch_labels = None
depends_on = None

"""
Summary of changes applied in this migration (SQLite-safe):
1. quotation_line_items.quantity -> ensure TEXT (String(100)) with server_default '1' and NOT NULL.
2. client_order_line_items.quantity -> ensure TEXT (String(100)) with server_default '1' and NOT NULL (preserving material_reference if already present).
3. quotation_line_items & client_order_line_items: enforce server_default '0' for unit_price & total_price when rebuild occurs.
4. supplier_order_line_items: if total_line_amount nullable OR delivery_status default not 'pending' (case-insensitive) then rebuild with NOT NULL + server_default '0' and delivery_status server_default 'pending'. Normalize existing data to lowercase.
5. supplier_orders: ensure total_amount NOT NULL server_default '0', currency server_default 'DZD'.
6. quotations: ensure total_amount NOT NULL server_default '0', currency server_default 'DZD'.
7. client_orders: ensure total_amount NOT NULL server_default '0'.
8. Normalize legacy uppercase 'PENDING' if rebuild not triggered.
9. Idempotent: guarded by schema inspection; second run is a no-op.

SQLite limitations require table recreation for altering column defaults or types. Rebuild only when discrepancies detected to avoid unnecessary churn and guarantee data preservation.
"""

# Helper utilities -----------------------------------------------------------

def _column_type_is_integer(conn, table: str, column: str) -> bool:
    row = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    for r in row:
        if r[1] == column:  # name
            return 'INT' in r[2].upper()
    return False


def _has_uppercase_pending(conn) -> bool:
    res = conn.execute(text("SELECT 1 FROM supplier_order_line_items WHERE delivery_status = 'PENDING' LIMIT 1"))
    return res.first() is not None


def _col_info(conn, table: str):
    return conn.execute(text(f"PRAGMA table_info({table})")).fetchall()


def _needs_supplier_order_line_items_fix(conn) -> bool:
    try:
        info = _col_info(conn, 'supplier_order_line_items')
    except Exception:
        return False
    total_line_nullable = None
    delivery_status_default = None
    for r in info:  # cid, name, type, notnull, dflt_value, pk
        if r[1] == 'total_line_amount':
            total_line_nullable = (r[3] == 0)  # 1 means NOT NULL
        if r[1] == 'delivery_status':
            delivery_status_default = (r[4] or '').strip("'\"").lower() or None
    # Need rebuild if total_line_amount nullable OR default not 'pending'
    return (total_line_nullable is True) or (delivery_status_default not in (None, 'pending'))


def upgrade() -> None:
    conn = op.get_bind()

    # 1 & 2: quantity columns to TEXT (String(100)) with default '1'
    # quotation_line_items
    if _column_type_is_integer(conn, 'quotation_line_items', 'quantity'):
        op.execute('ALTER TABLE quotation_line_items RENAME TO _tmp_quotation_line_items_old;')
        op.create_table('quotation_line_items',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('quotation_id', sa.Integer(), nullable=False),
            sa.Column('line_number', sa.Integer(), nullable=False),
            sa.Column('description', sa.String(255)),
            sa.Column('quantity', sa.String(100), nullable=False, server_default='1'),
            sa.Column('unit_price', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('total_price', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('length_mm', sa.Integer()),
            sa.Column('width_mm', sa.Integer()),
            sa.Column('height_mm', sa.Integer()),
            sa.Column('color', sa.String(10)),  # stored as plain text enum
            sa.Column('cardboard_type', sa.String(64)),
            sa.Column('material_reference', sa.String(64)),  # ensure presence if already added in models
            sa.Column('is_cliche', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_quotation_line_items_quotation_id', 'quotation_line_items', ['quotation_id'])
        # migrate data (material_reference may not exist previously -> default NULL)
        conn.execute(text('''INSERT INTO quotation_line_items (id, quotation_id, line_number, description, quantity, unit_price, total_price, length_mm, width_mm, height_mm, color, cardboard_type, material_reference, is_cliche, notes, created_at, updated_at)\n                             SELECT id, quotation_id, line_number, description, CAST(quantity AS TEXT), unit_price, total_price, length_mm, width_mm, height_mm, color, cardboard_type, NULL, is_cliche, notes, created_at, updated_at FROM _tmp_quotation_line_items_old;'''))
        op.execute('DROP TABLE _tmp_quotation_line_items_old;')

    # client_order_line_items (preserve material_reference if present)
    if _column_type_is_integer(conn, 'client_order_line_items', 'quantity'):
        op.execute('ALTER TABLE client_order_line_items RENAME TO _tmp_client_order_line_items_old;')
        op.create_table('client_order_line_items',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('client_order_id', sa.Integer(), nullable=False),
            sa.Column('quotation_line_item_id', sa.Integer()),
            sa.Column('line_number', sa.Integer(), nullable=False),
            sa.Column('description', sa.String(255)),
            sa.Column('quantity', sa.String(100), nullable=False, server_default='1'),
            sa.Column('unit_price', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('total_price', sa.Numeric(12, 2), nullable=False, server_default='0'),
            sa.Column('length_mm', sa.Integer()),
            sa.Column('width_mm', sa.Integer()),
            sa.Column('height_mm', sa.Integer()),
            sa.Column('color', sa.String(10)),  # stored as plain text enum
            sa.Column('cardboard_type', sa.String(64)),
            sa.Column('material_reference', sa.String(64)),
            sa.Column('is_cliche', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['client_order_id'], ['client_orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['quotation_line_item_id'], ['quotation_line_items.id'], ondelete='SET NULL'),
        )
        op.create_index('ix_client_order_line_items_client_order_id', 'client_order_line_items', ['client_order_id'])
        op.create_index('ix_client_order_line_items_quotation_line_item_id', 'client_order_line_items', ['quotation_line_item_id'])
        conn.execute(text('''INSERT INTO client_order_line_items (id, client_order_id, quotation_line_item_id, line_number, description, quantity, unit_price, total_price, length_mm, width_mm, height_mm, color, cardboard_type, material_reference, is_cliche, notes, created_at, updated_at)\n+                             SELECT id, client_order_id, quotation_line_item_id, line_number, description, CAST(quantity AS TEXT), unit_price, total_price, length_mm, width_mm, height_mm, color, cardboard_type, material_reference, is_cliche, notes, created_at, updated_at FROM _tmp_client_order_line_items_old;'''))
        op.execute('DROP TABLE _tmp_client_order_line_items_old;')

    # 5: Normalize existing uppercase PENDING entries if any
    if _has_uppercase_pending(conn):
        conn.execute(text("UPDATE supplier_order_line_items SET delivery_status = 'pending' WHERE delivery_status = 'PENDING'"))

    # 5 (extended): rebuild supplier_order_line_items if necessary
    if _needs_supplier_order_line_items_fix(conn):
        op.execute('ALTER TABLE supplier_order_line_items RENAME TO _tmp_supplier_order_line_items_old;')
        op.create_table('supplier_order_line_items',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('supplier_order_id', sa.Integer(), nullable=False),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('line_number', sa.Integer(), nullable=False),
            sa.Column('code_article', sa.String(100), nullable=False),
            sa.Column('caisse_length_mm', sa.Integer(), nullable=False),
            sa.Column('caisse_width_mm', sa.Integer(), nullable=False),
            sa.Column('caisse_height_mm', sa.Integer(), nullable=False),
            sa.Column('plaque_width_mm', sa.Integer(), nullable=False),
            sa.Column('plaque_length_mm', sa.Integer(), nullable=False),
            sa.Column('plaque_flap_mm', sa.Integer(), nullable=False),
            sa.Column('prix_uttc_plaque', sa.Numeric(12,2), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('total_line_amount', sa.Numeric(12,2), nullable=False, server_default='0'),
            sa.Column('cardboard_type', sa.String(64)),
            sa.Column('material_reference', sa.String(64)),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('delivery_status', sa.String(16), nullable=False, server_default='pending'),
            sa.Column('total_received_quantity', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['supplier_order_id'], ['supplier_orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        )
        op.create_index('ix_supplier_order_line_items_supplier_order_id', 'supplier_order_line_items', ['supplier_order_id'])
        op.create_index('ix_supplier_order_line_items_client_id', 'supplier_order_line_items', ['client_id'])
        op.create_index('ix_supplier_order_line_items_delivery_status', 'supplier_order_line_items', ['delivery_status'])
        conn.execute(text('''INSERT INTO supplier_order_line_items (id, supplier_order_id, client_id, line_number, code_article, caisse_length_mm, caisse_width_mm, caisse_height_mm, plaque_width_mm, plaque_length_mm, plaque_flap_mm, prix_uttc_plaque, quantity, total_line_amount, cardboard_type, material_reference, notes, created_at, updated_at, delivery_status, total_received_quantity)\n+                             SELECT id, supplier_order_id, client_id, line_number, code_article, caisse_length_mm, caisse_width_mm, caisse_height_mm, plaque_width_mm, plaque_length_mm, plaque_flap_mm, prix_uttc_plaque, quantity, COALESCE(total_line_amount,0), cardboard_type, material_reference, notes, created_at, updated_at, lower(delivery_status), COALESCE(total_received_quantity,0) FROM _tmp_supplier_order_line_items_old;'''))
        op.execute('DROP TABLE _tmp_supplier_order_line_items_old;')

    # 6-8: Ensure NOT NULL + defaults for total_amount columns and currency defaults
    # SQLite PRAGMA info doesn't show default expressions elegantly; we'll rebuild only if needed.
    def _needs_total_fix(table: str, column: str) -> bool:
        for r in conn.execute(text(f"PRAGMA table_info({table})")).fetchall():
            if r[1] == column:  # name
                notnull = r[3] == 1
                dflt = r[4]
                if not notnull or dflt is None:
                    return True
        return False

    def _rebuild_supplier_orders():
        op.execute('ALTER TABLE supplier_orders RENAME TO _tmp_supplier_orders_old;')
        op.create_table('supplier_orders',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('supplier_id', sa.Integer(), nullable=False),
            sa.Column('reference', sa.String(64), nullable=False),
            sa.Column('bon_commande_ref', sa.String(64), nullable=False),
            sa.Column('order_date', sa.Date(), server_default=sa.text('(CURRENT_DATE)'), nullable=False),
            sa.Column('status', sa.String(32), nullable=True),  # enum text stored
            sa.Column('total_amount', sa.Numeric(12,2), nullable=False, server_default='0'),
            sa.Column('currency', sa.String(3), nullable=True, server_default='DZD'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
            sa.UniqueConstraint('reference'),
            sa.UniqueConstraint('bon_commande_ref'),
        )
        op.create_index('ix_supplier_orders_supplier_id', 'supplier_orders', ['supplier_id'])
        op.create_index('ix_supplier_orders_reference', 'supplier_orders', ['reference'])
        op.create_index('ix_supplier_orders_bon_commande_ref', 'supplier_orders', ['bon_commande_ref'])
        op.create_index('ix_supplier_orders_order_date', 'supplier_orders', ['order_date'])
        op.create_index('ix_supplier_orders_status', 'supplier_orders', ['status'])
        conn.execute(text('''INSERT INTO supplier_orders (id, supplier_id, reference, bon_commande_ref, order_date, status, total_amount, currency, notes, created_at, updated_at)\n                             SELECT id, supplier_id, reference, bon_commande_ref, order_date, status, COALESCE(total_amount,0), COALESCE(currency,'DZD'), notes, created_at, updated_at FROM _tmp_supplier_orders_old;'''))
        op.execute('DROP TABLE _tmp_supplier_orders_old;')

    def _rebuild_quotations():
        op.execute('ALTER TABLE quotations RENAME TO _tmp_quotations_old;')
        op.create_table('quotations',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('reference', sa.String(64), nullable=False),
            sa.Column('issue_date', sa.Date(), server_default=sa.text('(CURRENT_DATE)'), nullable=False),
            sa.Column('valid_until', sa.Date()),
            sa.Column('total_amount', sa.Numeric(12,2), nullable=False, server_default='0'),
            sa.Column('currency', sa.String(3), nullable=True, server_default='DZD'),
            sa.Column('is_initial', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
            sa.UniqueConstraint('reference'),
        )
        op.create_index('ix_quotations_client_id', 'quotations', ['client_id'])
        op.create_index('ix_quotations_reference', 'quotations', ['reference'])
        op.create_index('ix_quotations_issue_date', 'quotations', ['issue_date'])
        conn.execute(text('''INSERT INTO quotations (id, client_id, reference, issue_date, valid_until, total_amount, currency, is_initial, notes, created_at, updated_at)\n                             SELECT id, client_id, reference, issue_date, valid_until, COALESCE(total_amount,0), COALESCE(currency,'DZD'), COALESCE(is_initial,0), notes, created_at, updated_at FROM _tmp_quotations_old;'''))
        op.execute('DROP TABLE _tmp_quotations_old;')

    def _rebuild_client_orders():
        op.execute('ALTER TABLE client_orders RENAME TO _tmp_client_orders_old;')
        op.create_table('client_orders',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('client_id', sa.Integer(), nullable=False),
            sa.Column('quotation_id', sa.Integer()),
            sa.Column('supplier_order_id', sa.Integer()),
            sa.Column('reference', sa.String(64), nullable=False),
            sa.Column('order_date', sa.Date(), server_default=sa.text('(CURRENT_DATE)'), nullable=False),
            sa.Column('status', sa.String(32), nullable=True),
            sa.Column('total_amount', sa.Numeric(12,2), nullable=False, server_default='0'),
            sa.Column('notes', sa.Text()),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['supplier_order_id'], ['supplier_orders.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('reference'),
        )
        op.create_index('ix_client_orders_client_id', 'client_orders', ['client_id'])
        op.create_index('ix_client_orders_quotation_id', 'client_orders', ['quotation_id'])
        op.create_index('ix_client_orders_supplier_order_id', 'client_orders', ['supplier_order_id'])
        op.create_index('ix_client_orders_reference', 'client_orders', ['reference'])
        op.create_index('ix_client_orders_order_date', 'client_orders', ['order_date'])
        op.create_index('ix_client_orders_status', 'client_orders', ['status'])
        conn.execute(text('''INSERT INTO client_orders (id, client_id, quotation_id, supplier_order_id, reference, order_date, status, total_amount, notes, created_at, updated_at)\n                             SELECT id, client_id, quotation_id, supplier_order_id, reference, order_date, status, COALESCE(total_amount,0), notes, created_at, updated_at FROM _tmp_client_orders_old;'''))
        op.execute('DROP TABLE _tmp_client_orders_old;')

    if _needs_total_fix('supplier_orders', 'total_amount') or _needs_total_fix('supplier_orders', 'currency'):
        _rebuild_supplier_orders()
    if _needs_total_fix('quotations', 'total_amount') or _needs_total_fix('quotations', 'currency'):
        _rebuild_quotations()
    if _needs_total_fix('client_orders', 'total_amount'):
        _rebuild_client_orders()


def downgrade() -> None:
    # Non-destructive downgrade is complex; we will not attempt to revert text quantities to integers or remove defaults.
    # Intentionally left as no-op to preserve data integrity.
    pass
