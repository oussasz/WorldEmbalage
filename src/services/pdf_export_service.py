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
            'plaque_width_mm': item.plaque_width_mm,
            'plaque_length_mm': item.plaque_length_mm,
            'plaque_flap_mm': item.plaque_flap_mm,
            'estimated_quantity': item.quantity,
            'grammage': item.cardboard_type or '',
            'cardboard_type': item.cardboard_type or '',
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


def export_finished_product_fiche(production_batch_id: int, quantity: int, 
                                 copy_number: int = 1, total_copies: int = 1, 
                                 dimensions: str | None = None) -> Path | None:
    """
    Export a finished product fiche to PDF using the PF.pdf template.
    
    Args:
        production_batch_id: The ID of the production batch
        quantity: The quantity for this specific fiche
        copy_number: The copy number (for multiple pallets)
        total_copies: Total number of copies being generated
        dimensions: Optional dimensions string from UI grid
        
    Returns:
        Path to the generated PDF file, or None if export failed
    """
    from models.production import ProductionBatch
    from models.orders import ClientOrder
    from models.clients import Client
    from sqlalchemy.orm import joinedload
    
    session = SessionLocal()
    try:
        # Get the production batch with related data
        batch = session.query(ProductionBatch).filter(ProductionBatch.id == production_batch_id).first()
        if not batch:
            return None
        
        # Get client order information with client data
        client_order = session.query(ClientOrder).options(
            joinedload(ClientOrder.client),
            joinedload(ClientOrder.line_items)
        ).filter(ClientOrder.id == batch.client_order_id).first()
        
        if not client_order:
            return None
        
        # Prepare data for PDF template
        product_data = _prepare_finished_product_data(batch, client_order, quantity, copy_number, total_copies, dimensions)
        
        # Generate PDF using template
        pdf_filler = PDFFormFiller()
        try:
            # Generate unique filename for this copy
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            client_name = client_order.client.name if client_order.client else 'client'
            filename = f"fiche_produit_fini_{client_name}_{quantity}u_copie{copy_number}_{timestamp}.pdf"
            
            output_path = pdf_filler.fill_finished_product_template(product_data, filename)
            return output_path
        except PDFFillError as e:
            print(f"PDF generation error: {e}")
            return None
            
    except Exception as e:
        print(f"Error exporting finished product fiche to PDF: {e}")
        return None
    finally:
        session.close()


def _prepare_finished_product_data(batch, client_order, quantity: int, copy_number: int, total_copies: int, dimensions_override: str | None = None) -> Dict[str, Any]:
    """Prepare finished product data for PDF template."""
    
    # Format production date
    production_date = ""
    if batch.production_date:
        if isinstance(batch.production_date, str):
            production_date = batch.production_date
        else:
            production_date = batch.production_date.strftime('%d/%m/%Y')
    
    # Get client name
    client_name = "Client non spécifié"
    if client_order and client_order.client:
        client_name = client_order.client.name
    
    # Use dimensions override from UI grid if provided, otherwise try database
    dimensions = dimensions_override or ""
    
    if not dimensions and client_order and client_order.line_items:
        # Get dimensions from the first line item (assuming all items have same dimensions)
        first_item = client_order.line_items[0]
        if first_item.length_mm and first_item.width_mm and first_item.height_mm:
            dimensions = f"{first_item.length_mm} x {first_item.width_mm} x {first_item.height_mm} mm"
        elif hasattr(first_item, 'description') and first_item.description:
            # Try to extract dimensions from description if available
            dimensions = first_item.description
    
    # If no dimensions found, use default
    if not dimensions:
        dimensions = "Dimensions non spécifiées"
    
    # Generate unique reference for this fiche
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    batch_ref = batch.batch_code or f"B{batch.id}"
    reference = f"FPF-{batch_ref}-{copy_number:03d}-{timestamp}"
    
    # Add copy information if multiple copies
    copy_info = ""
    if total_copies > 1:
        copy_info = f" (Copie {copy_number}/{total_copies})"
    
    return {
        'production_date': production_date,
        'client': client_name,
        'quantity': quantity,
        'dimensions': dimensions,
        'batch_code': batch.batch_code or '',
        'reference': reference,
        'copy_info': copy_info
    }
