"""
Professional PDF export service for supplier orders using templates.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, date
from config.database import SessionLocal
from models.orders import SupplierOrder
from models.suppliers import Supplier
from services.pdf_form_filler import PDFFormFiller, PDFFillError


def export_supplier_order_to_pdf(order_id: int) -> Path | None:
    """
    Export a supplier order to PDF using the page.pdf template.
    
    Args:
        order_id: The ID of the supplier order to export
        
    Returns:
        Path to the generated PDF file, or None if export failed
    """
    session = SessionLocal()
    try:
        # Get the supplier order with related data
        order = session.query(SupplierOrder).filter(SupplierOrder.id == order_id).first()
        if not order:
            return None
        
        # Get supplier information
        supplier = session.query(Supplier).filter(Supplier.id == order.supplier_id).first()
        if not supplier:
            return None
        
        # Prepare data for PDF template
        order_data = _prepare_order_data(order, supplier)
        
        # Generate PDF using template
        pdf_filler = PDFFormFiller()
        try:
            output_path = pdf_filler.fill_supplier_order_template(order_data)
            return output_path
        except PDFFillError as e:
            print(f"PDF generation error: {e}")
            return None
            
    except Exception as e:
        print(f"Error exporting supplier order to PDF: {e}")
        return None
    finally:
        session.close()


def _prepare_order_data(order: SupplierOrder, supplier: Supplier) -> Dict[str, Any]:
    """
    Prepare supplier order data for PDF template.
    
    Args:
        order: The SupplierOrder instance
        supplier: The Supplier instance
        
    Returns:
        Dictionary containing formatted data for PDF generation
    """
    # Format dates
    if order.order_date:
        if isinstance(order.order_date, date):
            order_date = order.order_date.strftime('%d/%m/%Y')
        else:
            order_date = str(order.order_date)
    else:
        order_date = ''
    
    # Prepare order items
    order_items = []
    for item in order.line_items:
        order_items.append({
            'reference': item.material_reference or '',
            'description': item.code_article or '',
            'length_mm': item.caisse_length_mm,
            'width_mm': item.caisse_width_mm,
            'height_mm': item.caisse_height_mm,
            'estimated_quantity': item.quantity,
            'grammage': item.cardboard_type or '',
            'unit_price': float(str(item.prix_uttc_plaque)) if item.prix_uttc_plaque else 0.0,
        })
    
    return {
        'reference': order.bon_commande_ref,
        'order_date': order_date,
        'expected_delivery_date': '',  # Not available in current model
        'supplier_name': supplier.name,
        'supplier_contact': supplier.contact_name or '',
        'supplier_email': supplier.email or '',
        'supplier_phone': supplier.phone or '',
        'order_items': order_items,
        'notes': order.notes or ''
    }
