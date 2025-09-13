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
    from models.orders import ClientOrder, Quotation
    from models.clients import Client
    from sqlalchemy.orm import joinedload
    
    session = SessionLocal()
    try:
        # Get the production batch with related data
        batch = session.query(ProductionBatch).filter(ProductionBatch.id == production_batch_id).first()
        if not batch:
            return None
        
        # Get client order information with client data and quotation
        client_order = session.query(ClientOrder).options(
            joinedload(ClientOrder.client),
            joinedload(ClientOrder.line_items),
            joinedload(ClientOrder.quotation).joinedload(Quotation.line_items)
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
    
    # Use dimensions override from UI grid if provided, otherwise try quotation description
    dimensions = dimensions_override or ""
    designation = ""  # explicit designation field for PF
    
    # PRIORITY: Try to get description/designation from quotation first
    if not dimensions and client_order and client_order.quotation and client_order.quotation.line_items:
        quotation_line_item = client_order.quotation.line_items[0]
        if quotation_line_item.description:
            dimensions = quotation_line_item.description
            designation = quotation_line_item.description
            print(f"DEBUG Product Sheet: Found direct quotation description: '{dimensions}'")
    
    # Fallback: Look for most recent quotation for the same client if no direct quotation link
    if not dimensions and client_order and client_order.client:
        from models.orders import Quotation, QuotationLineItem
        from sqlalchemy import desc
        from config.database import SessionLocal
        
        session = SessionLocal()
        try:
            most_recent_quotation = session.query(Quotation).filter(
                Quotation.client_id == client_order.client.id
            ).order_by(desc(Quotation.issue_date)).first()
            
            if most_recent_quotation and most_recent_quotation.line_items:
                quotation_line_item = most_recent_quotation.line_items[0]
                if quotation_line_item.description:
                    dimensions = quotation_line_item.description
                    designation = quotation_line_item.description
                    print(f"DEBUG Product Sheet: Found recent quotation description: '{dimensions}'")
        finally:
            session.close()
    
    # Fallback to client order line items
    if not dimensions and client_order and client_order.line_items:
        # Get dimensions from the first line item (assuming all items have same dimensions)
        first_item = client_order.line_items[0]
        if first_item.length_mm and first_item.width_mm and first_item.height_mm:
            dimensions = f"{first_item.length_mm} x {first_item.width_mm} x {first_item.height_mm} mm"
        elif hasattr(first_item, 'description') and first_item.description:
            # Try to extract dimensions from description if available
            dimensions = first_item.description
            if not designation:
                designation = first_item.description
    
    # If no dimensions found, use default
    if not dimensions:
        dimensions = "Dimensions non spécifiées"
        print(f"DEBUG Product Sheet: Using fallback description: '{dimensions}'")
    if not designation:
        designation = dimensions
    
    # Generate unique reference for this fiche using unified system
    from utils.reference_generator import generate_finished_product_reference
    reference = generate_finished_product_reference(f"COPIE{copy_number:03d}")
    
    # Add copy information if multiple copies
    copy_info = ""
    if total_copies > 1:
        copy_info = f" (Copie {copy_number}/{total_copies})"
    
    return {
        'production_date': production_date,
        'client': client_name,
        'quantity': quantity,
        'dimensions': dimensions,
        'designation': designation,
        'batch_code': batch.batch_code or '',
        'reference': reference,
        'copy_info': copy_info
    }


def export_raw_material_label(reception_ids: list[int], remark: str = "") -> Path | None:
    """
    Export a raw material label to PDF using the MP.pdf template.
    
    Args:
        reception_ids: List of reception IDs (for grouped receptions)
        remark: Optional remark to include on the label
        
    Returns:
        Path to the generated PDF file, or None if export failed
    """
    from models.orders import SupplierOrderLineItem, SupplierOrder, Reception
    from models.clients import Client
    from sqlalchemy.orm import joinedload
    
    session = SessionLocal()
    try:
        # Get the receptions
        receptions = session.query(Reception).filter(Reception.id.in_(reception_ids)).all()
        
        if not receptions:
            return None
        
        # Use the first reception as the primary one for extracting information
        primary_reception = receptions[0]
        supplier_order = primary_reception.supplier_order
        
        if not supplier_order:
            return None
        
        # Calculate total quantity from all receptions
        total_quantity = sum(r.quantity for r in receptions)
        
        # Get the most recent arrival date
        latest_date = None
        if receptions:
            for r in receptions:
                if r.reception_date:
                    latest_date = r.reception_date
                    break  # Use the first available date for now
        
        # Extract information from supplier order and line items
        line_items = supplier_order.line_items if hasattr(supplier_order, 'line_items') else []
        
        # Get client information from line items
        clients = set()
        plaque_dimensions = ""
        caisse_dimensions = ""
        total_ordered = 0
        is_cliche = False  # Default to False as SupplierOrderLineItem doesn't have is_cliche field
        
        for item in line_items:
            if hasattr(item, 'client') and item.client:
                clients.add(item.client.name)
            
            total_ordered += item.quantity
            
            # Get dimensions from the first line item
            if not plaque_dimensions and item.plaque_length_mm and item.plaque_width_mm:
                plaque_dimensions = f"{item.plaque_length_mm} x {item.plaque_width_mm} mm"
            
            if not caisse_dimensions and item.caisse_length_mm and item.caisse_width_mm and item.caisse_height_mm:
                caisse_dimensions = f"{item.caisse_length_mm} x {item.caisse_width_mm} x {item.caisse_height_mm} mm"
        
        # Calculate remaining quantity
        remaining_quantity = max(0, total_ordered - total_quantity)
        
        # Prepare data for PDF template
        label_data = _prepare_raw_material_label_data_simple(
            reception_ids, total_quantity, latest_date, supplier_order, 
            clients, plaque_dimensions, caisse_dimensions, is_cliche, 
            remaining_quantity, remark
        )
        
        # Generate PDF using template
        pdf_filler = PDFFormFiller()
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            client_names = "_".join(sorted(clients)) if clients else 'client'
            label_number = label_data.get('label_number', '000')
            filename = f"etiquette_mp_{client_names}_{label_number}_{timestamp}.pdf"
            
            output_path = pdf_filler.fill_raw_material_label_template(label_data, filename)
            return output_path
        except PDFFillError as e:
            print(f"PDF generation error: {e}")
            return None
            
    except Exception as e:
        print(f"Error exporting raw material label to PDF: {e}")
        return None
    finally:
        session.close()


def _prepare_raw_material_label_data_simple(reception_ids: list[int], total_quantity: int, latest_date, 
                                           supplier_order, clients: set, plaque_dimensions: str, 
                                           caisse_dimensions: str, is_cliche: bool, remaining_quantity: int, 
                                           remark: str) -> Dict[str, Any]:
    """Prepare raw material label data for PDF template."""
    
    # Format arrival date
    arrival_date = ""
    if latest_date:
        if isinstance(latest_date, str):
            arrival_date = latest_date
        else:
            arrival_date = latest_date.strftime('%d/%m/%Y')
    
    # Get client names
    client_name = ", ".join(sorted(clients)) if clients else "Client non spécifié"
    
    # Try to get quotation description for the first client
    quotation_description = ""
    if supplier_order and supplier_order.line_items:
        from models.orders import Quotation, QuotationLineItem
        from sqlalchemy import desc
        from config.database import SessionLocal
        
        session = SessionLocal()
        try:
            # Get the first client from supplier order line items
            first_line_item = supplier_order.line_items[0]
            if hasattr(first_line_item, 'client') and first_line_item.client:
                client = first_line_item.client
                
                # Look for most recent quotation for this client
                most_recent_quotation = session.query(Quotation).filter(
                    Quotation.client_id == client.id
                ).order_by(desc(Quotation.issue_date)).first()
                
                if most_recent_quotation and most_recent_quotation.line_items:
                    quotation_line_item = most_recent_quotation.line_items[0]
                    if quotation_line_item.description:
                        quotation_description = quotation_line_item.description
                        print(f"DEBUG Raw Material Label: Found quotation description: '{quotation_description}' for client {client.name}")
        except Exception as e:
            print(f"DEBUG Raw Material Label: Error getting quotation description: {e}")
        finally:
            session.close()
    
    if not quotation_description:
        quotation_description = caisse_dimensions or "Cartons"
        print(f"DEBUG Raw Material Label: Using fallback description: '{quotation_description}'")
    
    # Generate unique label number using unified system
    from utils.reference_generator import generate_raw_material_label_reference
    ids_str = "_".join(map(str, reception_ids))
    label_number = generate_raw_material_label_reference(ids_str)
    
    # Get bon de commande reference
    bon_commande = ""
    if supplier_order:
        bon_commande = supplier_order.bon_commande_ref or supplier_order.reference or ""
    
    return {
        'arrival_date': arrival_date,
        'client': client_name,
        'quantity': total_quantity,
        'label_number': label_number,
        'plaque_dimensions': plaque_dimensions or "Non spécifiées",
        'caisse_dimensions': quotation_description,  # Use quotation description instead of raw dimensions
        'cliche': "Oui" if is_cliche else "Non",
        'remark': remark,
        'bon_commande': bon_commande,
        'remaining_quantity': remaining_quantity
    }
