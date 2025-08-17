"""
PDF Export Service for supplier orders and other document exports.
Provides professional PDF generation using templates.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from pathlib import Path

# Type checking imports - always available for type hints
if TYPE_CHECKING:
    from reportlab.lib.pagesizes import A4 as A4_TYPE
    from reportlab.platypus import SimpleDocTemplate as SimpleDocumentTemplate_TYPE
    from reportlab.platypus import Table as Table_TYPE
    from reportlab.platypus import TableStyle as TableStyle_TYPE
    from reportlab.platypus import Paragraph as Paragraph_TYPE
    from reportlab.platypus import Spacer as Spacer_TYPE
    from reportlab.lib.styles import getSampleStyleSheet as getSampleStyleSheet_TYPE
    from reportlab.lib.styles import ParagraphStyle as ParagraphStyle_TYPE
    from reportlab.lib.units import mm as mm_TYPE, cm as cm_TYPE
    from reportlab.lib import colors as colors_TYPE
    from reportlab.lib.enums import TA_CENTER as TA_CENTER_TYPE
    from reportlab.lib.enums import TA_LEFT as TA_LEFT_TYPE
    from reportlab.lib.enums import TA_RIGHT as TA_RIGHT_TYPE

# Runtime imports with fallback
try:
    import reportlab.lib.pagesizes as pagesizes
    import reportlab.platypus as platypus
    import reportlab.lib.styles as styles
    import reportlab.lib.units as units
    import reportlab.lib.colors as colors
    import reportlab.lib.enums as enums
    from reportlab.pdfgen import canvas
    
    # Extract the actual objects we need
    A4 = pagesizes.A4
    SimpleDocTemplate = platypus.SimpleDocTemplate
    Table = platypus.Table
    TableStyle = platypus.TableStyle
    Paragraph = platypus.Paragraph
    Spacer = platypus.Spacer
    getSampleStyleSheet = styles.getSampleStyleSheet
    ParagraphStyle = styles.ParagraphStyle
    mm = units.mm
    cm = units.cm
    TA_CENTER = enums.TA_CENTER
    TA_LEFT = enums.TA_LEFT
    TA_RIGHT = enums.TA_RIGHT
    
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("ReportLab not installed. PDF generation will not be available.")
    REPORTLAB_AVAILABLE = False
    # These will remain None when ReportLab isn't available
    # Type checker won't see these at runtime when REPORTLAB_AVAILABLE is True

from config.database import SessionLocal
from models.orders import SupplierOrder, SupplierOrderLineItem


class PDFExportService:
    """Service for generating professional PDF exports"""
    
    def __init__(self):
        self.output_dir = Path("generated_reports")
        self.template_dir = Path("template")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure output directory exists"""
        self.output_dir.mkdir(exist_ok=True)
    
    def export_supplier_order_pdf(self, supplier_order_id: int) -> Optional[str]:
        """
        Export a supplier order as a professional PDF document.
        
        Args:
            supplier_order_id: ID of the supplier order to export
            
        Returns:
            Path to the generated PDF file, or None if generation failed
        """
        if not REPORTLAB_AVAILABLE:
            print("ReportLab is not available. Cannot generate PDF.")
            return None
            
        try:
            # Get supplier order from database
            session = SessionLocal()
            try:
                supplier_order = session.get(SupplierOrder, supplier_order_id)
                if not supplier_order:
                    raise ValueError(f"Supplier order {supplier_order_id} not found")
                
                # Generate PDF filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"commande_matiere_{supplier_order.bon_commande_ref}_{timestamp}.pdf"
                output_path = self.output_dir / filename
                
                # Create PDF document
                doc = SimpleDocTemplate(  # type: ignore
                    str(output_path),
                    pagesize=A4,  # type: ignore
                    rightMargin=2*cm,  # type: ignore
                    leftMargin=2*cm,  # type: ignore
                    topMargin=2*cm,  # type: ignore
                    bottomMargin=2*cm  # type: ignore
                )
                
                # Build document content
                story = self._build_supplier_order_content(supplier_order)
                
                # Generate PDF
                doc.build(story)
                
                return str(output_path)
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return None
    
    def _build_supplier_order_content(self, supplier_order: SupplierOrder) -> List[Any]:
        """Build the content for supplier order PDF"""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not available")
            
        story = []
        styles = getSampleStyleSheet()  # type: ignore
        
        # Custom styles
        title_style = ParagraphStyle(  # type: ignore
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,  # type: ignore
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(  # type: ignore
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Document title
        story.append(Paragraph("COMMANDE DE MATIÈRE PREMIÈRE", title_style))  # type: ignore
        story.append(Spacer(1, 20))  # type: ignore
        
        # Order information
        story.append(Paragraph("Informations de Commande", header_style))  # type: ignore
        
        order_data = [
            ["Référence BC:", supplier_order.bon_commande_ref or "N/A"],
            ["Fournisseur:", supplier_order.supplier.name if supplier_order.supplier else "N/A"],
            ["Date de commande:", str(supplier_order.order_date) if supplier_order.order_date else "N/A"],
            ["Statut:", self._get_status_display(supplier_order.status)],
        ]
        
        if hasattr(supplier_order.supplier, 'contact_name') and supplier_order.supplier.contact_name:
            order_data.append(["Contact:", supplier_order.supplier.contact_name])
        
        if hasattr(supplier_order.supplier, 'phone') and supplier_order.supplier.phone:
            order_data.append(["Téléphone:", supplier_order.supplier.phone])
        
        order_table = Table(order_data, colWidths=[4*cm, 10*cm])  # type: ignore
        order_table.setStyle(TableStyle([  # type: ignore
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(order_table)
        story.append(Spacer(1, 30))  # type: ignore
        
        # Line items table
        if hasattr(supplier_order, 'line_items') and supplier_order.line_items:
            story.append(Paragraph("Détails des Plaques", header_style))  # type: ignore
            
            # Table headers as specified by user
            headers = [
                "N°",
                "Référence de plaques", 
                "Mesure de caisse",
                "Désignation de plaque dimensions",
                "Prix UTTC",
                "Quantity"
            ]
            
            # Prepare data rows
            table_data = [headers]
            
            for idx, line_item in enumerate(supplier_order.line_items, 1):
                # Extract data with safe fallbacks
                line_number = str(idx)
                
                # Référence de plaques
                plaque_ref = getattr(line_item, 'material_reference', '') or 'N/A'
                
                # Mesure de caisse (L×l×H)
                caisse_l = getattr(line_item, 'caisse_length_mm', 0) or 0
                caisse_w = getattr(line_item, 'caisse_width_mm', 0) or 0
                caisse_h = getattr(line_item, 'caisse_height_mm', 0) or 0
                mesure_caisse = f"{caisse_l}×{caisse_w}×{caisse_h}"
                
                # Désignation de plaque dimensions (L×l×R)
                plaque_l = getattr(line_item, 'plaque_length_mm', 0) or 0
                plaque_w = getattr(line_item, 'plaque_width_mm', 0) or 0
                plaque_r = getattr(line_item, 'plaque_flap_mm', 0) or 0
                designation = f"{plaque_l}×{plaque_w}×{plaque_r}"
                
                # Prix UTTC
                prix_uttc = getattr(line_item, 'prix_uttc_plaque', 0) or 0
                prix_str = f"{float(prix_uttc):,.2f} DA"
                
                # Quantity
                quantity = str(getattr(line_item, 'quantity', 0) or 0)
                
                table_data.append([
                    line_number,
                    plaque_ref,
                    mesure_caisse,
                    designation,
                    prix_str,
                    quantity
                ])
            
            # Create table with appropriate column widths
            col_widths = [1.5*cm, 3*cm, 3*cm, 4*cm, 2.5*cm, 2*cm]  # type: ignore
            items_table = Table(table_data, colWidths=col_widths)  # type: ignore
            
            # Apply table styling
            items_table.setStyle(TableStyle([  # type: ignore
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # type: ignore
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # type: ignore
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # N° column
                ('ALIGN', (1, 1), (3, -1), 'LEFT'),    # Text columns
                ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Price and quantity columns
                
                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # type: ignore
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),  # type: ignore
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 20))  # type: ignore
        
        # Summary information
        if hasattr(supplier_order, 'line_items') and supplier_order.line_items:
            story.append(Paragraph("Résumé", header_style))  # type: ignore
            
            total_quantity = sum(getattr(item, 'quantity', 0) or 0 for item in supplier_order.line_items)
            total_amount = sum(
                (getattr(item, 'prix_uttc_plaque', 0) or 0) * (getattr(item, 'quantity', 0) or 0) 
                for item in supplier_order.line_items
            )
            
            summary_data = [
                ["Nombre total de plaques:", str(total_quantity)],
                ["Nombre de lignes:", str(len(supplier_order.line_items))],
                ["Montant total:", f"{float(total_amount):,.2f} DA"],
            ]
            
            summary_table = Table(summary_data, colWidths=[4*cm, 10*cm])  # type: ignore
            summary_table.setStyle(TableStyle([  # type: ignore
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(summary_table)
        
        # Notes section
        if supplier_order.notes:
            story.append(Spacer(1, 20))  # type: ignore
            story.append(Paragraph("Notes", header_style))  # type: ignore
            story.append(Paragraph(supplier_order.notes, styles['Normal']))  # type: ignore
        
        # Footer with generation timestamp
        story.append(Spacer(1, 30))  # type: ignore
        footer_text = f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"
        footer_style = ParagraphStyle(  # type: ignore
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,  # type: ignore
            textColor=colors.grey  # type: ignore
        )
        story.append(Paragraph(footer_text, footer_style))  # type: ignore
        
        return story
    
    def _get_status_display(self, status) -> str:
        """Get human-readable status display"""
        if not status:
            return "N/A"
        
        status_map = {
            'commande_initial': 'Initial',
            'commande_passee': 'Commandé', 
            'commande_arrivee': 'Reçu'
        }
        
        if hasattr(status, 'value'):
            return status_map.get(status.value, str(status.value))
        
        return status_map.get(str(status), str(status))


def export_supplier_order_to_pdf(supplier_order_id: int) -> Optional[str]:
    """
    Convenience function to export a supplier order to PDF.
    
    Args:
        supplier_order_id: ID of the supplier order to export
        
    Returns:
        Path to the generated PDF file, or None if generation failed
    """
    if not REPORTLAB_AVAILABLE:
        return None
        
    service = PDFExportService()
    return service.export_supplier_order_pdf(supplier_order_id)
