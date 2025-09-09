from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path
from datetime import date
from config.settings import settings
import io


def build_delivery_note_pdf(reference: str, client_name: str, delivery_date: date, lines: list[dict], client_details: str = "") -> Path:
    """
    Generate a delivery note PDF using the page.pdf template as base
    
    Args:
        reference: Delivery note reference number
        client_name: Client name
        delivery_date: Delivery date
        lines: List of product lines with keys: designation, dimensions, quantity
        client_details: Full client details block
    """
    # Paths
    template_path = Path(__file__).parent.parent.parent.parent / "template" / "page.pdf"
    output_dir = settings.reports_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = delivery_date.strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f"bon_livraison_{reference}_{timestamp}.pdf"
    
    # Verify template exists
    if not template_path.exists():
        raise FileNotFoundError(f"Template PDF not found: {template_path}")
    
    # Create overlay content
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    # Set up fonts
    can.setFont("Helvetica-Bold", 18)
    
    # Title - BON DE LIVRAISON (centered, positioned below company header)
    title = "BON DE LIVRAISON"
    title_width = can.stringWidth(title, "Helvetica-Bold", 18)
    can.drawString((width - title_width) / 2, height - 200, title)
    
    # Reference and Date (positioned below title)
    can.setFont("Helvetica-Bold", 12)
    can.drawString(50, height - 240, f"Référence: {reference}")
    can.drawString(50, height - 260, f"Date: {delivery_date.strftime('%d/%m/%Y')}")
    
    # Client block (positioned below reference)
    can.setFont("Helvetica-Bold", 11)
    y_position = height - 300
    
    if client_details:
        # Use full client details if provided
        client_lines = client_details.split('\n')
        for line in client_lines:
            if line.strip():
                can.drawString(50, y_position, line.strip())
                y_position -= 15
    else:
        # Fallback to just client name
        can.drawString(50, y_position, f"Client: {client_name}")
        y_position -= 15
    
    # Intro text
    y_position -= 20
    can.setFont("Helvetica", 10)
    intro_text = "Nous avons le plaisir de vous livrer, conformément à votre commande, les produits mentionnés ci-dessous."
    
    # Word wrap the intro text
    words = intro_text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if can.stringWidth(test_line, "Helvetica", 10) < width - 100:
            line = test_line
        else:
            can.drawString(50, y_position, line.strip())
            y_position -= 15
            line = word + " "
    if line.strip():
        can.drawString(50, y_position, line.strip())
        y_position -= 30
    
    # Table header
    table_y = y_position
    can.setFont("Helvetica-Bold", 10)
    
    # Table dimensions
    col_widths = [30, 200, 120, 80]  # N°, Désignation, Dimensions, Quantité
    col_x_positions = [50, 80, 280, 400]
    
    # Draw table header background
    can.setFillColor(colors.lightgrey)
    can.rect(50, table_y - 20, sum(col_widths), 20, fill=1, stroke=1)
    
    # Draw table header text
    can.setFillColor(colors.black)
    can.drawString(col_x_positions[0] + 5, table_y - 15, "N°")
    can.drawString(col_x_positions[1] + 5, table_y - 15, "Désignation de caisse")
    can.drawString(col_x_positions[2] + 5, table_y - 15, "Dimensions")
    can.drawString(col_x_positions[3] + 5, table_y - 15, "Quantité")
    
    # Draw table data
    can.setFont("Helvetica", 9)
    row_height = 20
    current_y = table_y - 20
    
    for i, line in enumerate(lines, 1):
        current_y -= row_height
        
        # Alternate row background
        if i % 2 == 0:
            can.setFillColor(colors.lightgrey)
            can.rect(50, current_y, sum(col_widths), row_height, fill=1, stroke=0)
        
        # Draw cell borders
        can.setStrokeColor(colors.black)
        can.setLineWidth(0.5)
        for j, col_width in enumerate(col_widths):
            x_pos = col_x_positions[j]
            can.rect(x_pos, current_y, col_width if j < len(col_widths) - 1 else col_widths[j], row_height, fill=0, stroke=1)
        
        # Draw text
        can.setFillColor(colors.black)
        designation = str(line.get('designation', line.get('description', '')))
        dimensions = str(line.get('dimensions', ''))
        quantity = str(line.get('quantity', ''))
        
        can.drawString(col_x_positions[0] + 5, current_y + 6, str(i))
        
        # Handle long designation text
        if len(designation) > 30:
            designation = designation[:27] + "..."
        can.drawString(col_x_positions[1] + 5, current_y + 6, designation)
        
        can.drawString(col_x_positions[2] + 5, current_y + 6, dimensions)
        can.drawString(col_x_positions[3] + 5, current_y + 6, quantity)
    
    # Footer text
    footer_y = current_y - 40
    can.setFont("Helvetica", 10)
    footer_text = "Veuillez vérifier soigneusement la quantité et les dimensions à la réception."
    can.drawString(50, footer_y, footer_text)
    
    # Signature block (right aligned)
    signature_y = footer_y - 60
    can.setFont("Helvetica", 10)
    signature_text = "SIGNATURE"
    date_text = f"Béjaïa le : {delivery_date.strftime('%d/%m/%Y')}"
    
    # Right align the signature block
    signature_width = can.stringWidth(signature_text, "Helvetica", 10)
    date_width = can.stringWidth(date_text, "Helvetica", 10)
    max_width = max(signature_width, date_width)
    
    can.drawString(width - max_width - 50, signature_y, signature_text)
    can.drawString(width - max_width - 50, signature_y - 20, date_text)
    
    can.save()
    
    # Move to the beginning of the BytesIO buffer
    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    
    # Read the template PDF
    template_pdf = PdfReader(str(template_path))
    
    # Create a new PDF with the overlay
    output_pdf = PdfWriter()
    
    # Get the first page of the template
    template_page = template_pdf.pages[0]
    
    # Merge the overlay onto the template page
    template_page.merge_page(overlay_pdf.pages[0])
    
    # Add the merged page to the output
    output_pdf.add_page(template_page)
    
    # Write the result to file
    with open(output_path, 'wb') as output_file:
        output_pdf.write(output_file)
    
    return output_path


__all__ = ['build_delivery_note_pdf']
