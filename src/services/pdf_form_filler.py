"""
PDF Form Filler Service for populating PDF templates with data.
This service handles filling PDF forms using PyPDF2.
"""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal
from typing import Any, Dict
import tempfile
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from config.settings import settings


class PDFFillError(Exception):
    """Exception raised when PDF filling fails."""
    pass


class PDFFormFiller:
    """Service for filling PDF forms with data."""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent.parent / "template"
        self.output_dir = settings.reports_dir
        
    def _ensure_pypdf_installed(self) -> bool:
        """Ensure PyPDF2 is installed, install if needed."""
        try:
            import PyPDF2  # type: ignore
            return True
        except ImportError:
            try:
                # Try to install PyPDF2
                subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
                import PyPDF2  # type: ignore
                return True
            except (subprocess.CalledProcessError, ImportError):
                return False
    
    def fill_devis_template(self, quotation_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the Devis PDF template with quotation data.
        
        Args:
            quotation_data: Dictionary containing quotation information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "Devie.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            ref = quotation_data.get('reference', 'devis')
            timestamp = date.today().strftime('%Y%m%d')
            output_filename = f"devis_{ref}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_with_pypdf(template_path, quotation_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_with_overlay(template_path, quotation_data, output_path)
    
    def _fill_with_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill PDF using PyPDF2 form fields."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            raise PDFFillError("PyPDF2 not available")
        
        try:
            with open(template_path, 'rb') as template_file:
                pdf_reader = PyPDF2.PdfReader(template_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                # Check if PDF has form fields
                if pdf_reader.get_fields():
                    # Fill form fields
                    field_data = self._prepare_form_data(data)
                    
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    
                    # Update form fields
                    pdf_writer.update_page_form_field_values(
                        pdf_writer.pages[0], field_data
                    )
                    
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                else:
                    # No form fields, use overlay method
                    return self._fill_with_overlay(template_path, data, output_path)
                    
        except Exception as e:
            raise PDFFillError(f"Failed to fill PDF with PyPDF2: {str(e)}")
        
        return output_path
    
    def _fill_with_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill PDF by creating an overlay with positioned text."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            # Fallback to simple copy with a warning
            shutil.copy2(template_path, output_path)
            print(f"Warning: PyPDF2 not available. Template copied to: {output_path}")
            return output_path
        
        try:
            # Create overlay with text
            overlay_path = self._create_text_overlay(data)
            
            # Merge overlay with template
            with open(template_path, 'rb') as template_file, \
                 open(overlay_path, 'rb') as overlay_file:
                
                template_pdf = PyPDF2.PdfReader(template_file)
                overlay_pdf = PyPDF2.PdfReader(overlay_file)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                # Merge first page
                template_page = template_pdf.pages[0]
                overlay_page = overlay_pdf.pages[0]
                template_page.merge_page(overlay_page)
                pdf_writer.add_page(template_page)
                
                # Add remaining pages if any
                for i in range(1, len(template_pdf.pages)):
                    pdf_writer.add_page(template_pdf.pages[i])
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            # Clean up temporary overlay file
            Path(overlay_path).unlink(missing_ok=True)
            
        except Exception as e:
            raise PDFFillError(f"Failed to create PDF overlay: {str(e)}")
        
        return output_path
    
    def _create_text_overlay(self, data: Dict[str, Any]) -> str:
        """Create a transparent PDF overlay with positioned text."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        
        try:
            c = canvas.Canvas(temp_path, pagesize=A4)
            width, height = A4
            
            # Set font
            c.setFont("Helvetica", 10)
            
            # Position text fields based on user-provided coordinates
            field_map = {
                "devie_number": data.get('reference', ''),
                "client_phone": data.get('client_phone', ''),
                "client_email": data.get('client_email', ''),
                "client_address": data.get('client_address', ''),
                "client_company": data.get('client_name', ''),
                "devie_date": data.get('issue_date', '')
            }

            coordinates = [
                {"field": "devie_number", "x": 100, "y": 200},
                {"field": "client_phone", "x": 400, "y": 180},
                {"field": "client_email", "x": 400, "y": 200},
                {"field": "client_address", "x": 400, "y": 220},
                {"field": "client_company", "x": 100, "y": 220},
                {"field": "devie_date", "x": 485, "y": 150}
            ]

            for item in coordinates:
                field_name = item["field"]
                if field_name in field_map:
                    c.drawString(item["x"], height - item["y"], str(field_map[field_name]))

            # Line items table
            if 'line_items' in data:
                is_initial = data.get('is_initial', False)
                
                if is_initial:
                    table_data = [["Description", "Couleur", "Cliché", "Quantité Min.", "UTTC"]]
                else:
                    table_data = [["Description", "Couleur", "Cliché", "Qté", "UTTC", "Total"]]
                
                total = Decimal('0')
                
                for item in data['line_items']:
                    # Extract numeric quantity for calculations
                    import re
                    quantity_str = str(item.get('quantity', '0'))
                    numbers = re.findall(r'\d+', quantity_str)
                    numeric_quantity = int(numbers[-1]) if numbers else 0
                    
                    line_total = Decimal(str(item.get('unit_price', 0))) * Decimal(str(numeric_quantity))
                    cliche_status = "Oui" if item.get('is_cliche') else "Non"
                    
                    if is_initial:
                        # For initial devis, show minimum quantity
                        table_data.append([
                            str(item.get('description', '')),
                            str(item.get('color', '')),
                            cliche_status,
                            str(item.get('quantity', '')),  # Display "à partir de X"
                            f"{item.get('unit_price', 0):.2f}"
                        ])
                    else:
                        table_data.append([
                            str(item.get('description', '')),
                            str(item.get('color', '')),
                            cliche_status,
                            str(item.get('quantity', '')),  # Display original quantity string
                            f"{item.get('unit_price', 0):.2f}",
                            f"{line_total:.2f}"
                        ])
                        total += line_total

                # Create and style the table
                table = Table(table_data, colWidths=[180, 60, 50, 50, 70, 80])
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#BBDEFB")]),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])

                table.setStyle(style)

                # Draw the table on the canvas
                table.wrapOn(c, width, height)
                table.drawOn(c, 60, height - 370)

                # Total (only show for non-initial devis)
                if not data.get('is_initial', False):
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(400, height - 450 - 30, f"TOTAL: {total:.2f} DA")
                else:
                    c.setFont("Helvetica-Oblique", 9)
                    c.drawString(400, height - 450 - 30, "Devis Initial - Quantités minimales indiquées")

            c.showPage()
            c.save()
            
        except Exception as e:
            raise PDFFillError(f"Failed to create text overlay: {str(e)}")
        finally:
            # Close the file descriptor
            import os
            os.close(temp_fd)
        
        return temp_path
    
    def _prepare_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for PDF form fields."""
        form_data = {}
        
        # Map data to common form field names
        field_mappings = {
            'reference': ['reference', 'ref', 'numero', 'number'],
            'client_name': ['client', 'client_name', 'customer'],
            'issue_date': ['date', 'issue_date', 'date_emission'],
            'valid_until': ['valid_until', 'validity', 'expiry'],
            'total_amount': ['total', 'total_amount', 'amount'],
            'notes': ['notes', 'remarks', 'comments']
        }
        
        for data_key, form_fields in field_mappings.items():
            if data_key in data:
                value = str(data[data_key])
                for field_name in form_fields:
                    form_data[field_name] = value
        
        return form_data


__all__ = ['PDFFormFiller', 'PDFFillError']
