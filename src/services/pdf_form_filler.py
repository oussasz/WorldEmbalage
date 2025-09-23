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
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
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
    
    def fill_material_label_template(self, label_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the material label PDF template with raw material data.
        
        Args:
            label_data: Dictionary containing material label information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "Fiche matiere première.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            label_num = label_data.get('label_number', 'MP')
            timestamp = date.today().strftime('%Y%m%d_%H%M%S')
            output_filename = f"etiquette_matiere_{label_num}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_material_label_pypdf(template_path, label_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_material_label_overlay(template_path, label_data, output_path)
    
    def _fill_material_label_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill material label PDF using PyPDF2 form fields."""
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
                    field_data = self._prepare_material_label_form_data(data)
                    
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
                    return self._fill_material_label_overlay(template_path, data, output_path)
                    
        except Exception as e:
            raise PDFFillError(f"Failed to fill material label PDF with PyPDF2: {str(e)}")
        
        return output_path
    
    def _fill_material_label_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill material label PDF by creating an overlay with positioned text."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            # Fallback to simple copy with a warning
            shutil.copy2(template_path, output_path)
            print(f"Warning: PyPDF2 not available. Template copied to: {output_path}")
            return output_path
        
        try:
            # Create overlay with text
            overlay_path = self._create_material_label_overlay(data)
            
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
            raise PDFFillError(f"Failed to create material label PDF overlay: {str(e)}")
        
        return output_path
    
    def _create_material_label_overlay(self, data: Dict[str, Any]) -> str:
        """Create a transparent PDF overlay with positioned text for material labels."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        
        try:
            c = canvas.Canvas(temp_path, pagesize=A4)
            width, height = A4
            

            # Set font
            c.setFont("Helvetica", 10)
            
            # Position text fields for material label (adjust coordinates based on template layout)
            field_map = {
                "last_arrival_date": data.get('last_arrival_date', ''),
                "client_name": data.get('client_name', ''),
                "current_stock_quantity": data.get('current_stock_quantity', ''),
                "label_number": data.get('label_number', ''),
                "designation": data.get('designation') or data.get('description') or data.get('caisse_dimensions', ''),
                "plaque_dimensions": data.get('plaque_dimensions', ''),
                "caisse_dimensions": data.get('caisse_dimensions', ''),
                "cliche_status": data.get('cliche_status', ''),
                "remarks": data.get('remarks', ''),
                "bon_commande_number": data.get('bon_commande_number', ''),
                "remaining_quantity": data.get('remaining_quantity', '')
            }

            # Coordinates for material label fields (adjust based on template)
            # These coordinates are positioned for a typical form layout
            coordinates = [
                {"field": "last_arrival_date", "x": 263, "y": 366, "font_size": 10},
                {"field": "client_name", "x": 143.33, "y": 418.67, "font_size": 15},
                {"field": "current_stock_quantity", "x": 162, "y": 520, "font_size": 12},
                {"field": "label_number", "x": 447, "y": 514, "font_size": 12},
                {"field": "designation", "x": 150, "y": 540, "font_size": 10},
                {"field": "plaque_dimensions", "x": 238, "y": 571, "font_size": 12},
                {"field": "caisse_dimensions", "x": 233, "y": 622, "font_size": 12},
                {"field": "cliche_status", "x": 147, "y": 694, "font_size": 12},
                {"field": "remarks", "x": 357, "y": 694, "font_size": 12},
                {"field": "bon_commande_number", "x": 233, "y": 746, "font_size": 12},
                {"field": "remaining_quantity", "x": 354, "y": 746, "font_size": 12}
            ]

            # Add labels first
            c.setFont("Helvetica-Bold", 10)
            for item in coordinates:
                if "label" in item:
                    c.drawString(50, height - item["y"], item["label"])

            for item in coordinates:
                field_name = item["field"]
                if field_name in field_map and field_map[field_name]:
                    # Set font size
                    font_size = item.get("font_size", 10)
                    
                    # Set font styles for different fields
                    if field_name == "client_name":
                        c.setFont("Helvetica-Bold", font_size)
                    else:
                        c.setFont("Helvetica", font_size)
                    
                    # Handle multi-line text for remarks
                    if field_name == "remarks" and len(str(field_map[field_name])) > 50:
                        # Split long remarks into multiple lines
                        remarks_text = str(field_map[field_name])
                        lines = []
                        words = remarks_text.split()
                        current_line = ""
                        for word in words:
                            test_line = current_line + (" " if current_line else "") + word
                            if c.stringWidth(test_line, "Helvetica", font_size) <= 200:  # Max width
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                        if current_line:
                            lines.append(current_line)
                        
                        # Draw each line
                        y_pos = height - item["y"]
                        for line in lines:
                            c.drawString(item["x"], y_pos, line)
                            y_pos -= 15
                    else:
                        c.drawString(item["x"], height - item["y"], str(field_map[field_name]))

            c.showPage()
            c.save()
            
        except Exception as e:
            raise PDFFillError(f"Failed to create material label overlay: {str(e)}")
        finally:
            # Close the file descriptor
            import os
            os.close(temp_fd)
        
        return temp_path
    
    def _prepare_material_label_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for material label PDF form fields."""
        form_data = {}
        
        # Map data to common form field names for material labels
        field_mappings = {
            'last_arrival_date': ['derniere_date_arrivee', 'date_arrivee', 'arrival_date'],
            'client_name': ['client', 'client_name', 'customer'],
            'current_stock_quantity': ['quantite', 'quantity', 'stock_quantity'],
            'label_number': ['etiquette', 'label_number', 'numero_etiquette'],
            'designation': ['designation', 'description', 'designation_produit'],
            'plaque_dimensions': ['dimension_plaque', 'plaque_dim', 'plaque_dimensions'],
            'caisse_dimensions': ['dimension_caisse', 'caisse_dim', 'caisse_dimensions'],
            'cliche_status': ['cliche', 'cliche_status', 'is_cliche'],
            'remarks': ['remarque', 'remarks', 'comments'],
            'bon_commande_number': ['bon_commande', 'order_number', 'commande_ref'],
            'remaining_quantity': ['reste', 'remaining', 'remaining_quantity']
        }
        
        for data_key, form_fields in field_mappings.items():
            if data_key in data:
                value = str(data[data_key])
                for field_name in form_fields:
                    form_data[field_name] = value
        
        return form_data

    def fill_supplier_order_template(self, order_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the supplier order PDF template with order data.
        
        Args:
            order_data: Dictionary containing supplier order information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "page.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            ref = order_data.get('reference', 'commande')
            timestamp = date.today().strftime('%Y%m%d_%H%M%S')
            output_filename = f"commande_matiere_{ref}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_supplier_order_pypdf(template_path, order_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_supplier_order_overlay(template_path, order_data, output_path)
    
    def _fill_supplier_order_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill supplier order PDF using PyPDF2 form fields."""
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
                    field_data = self._prepare_supplier_order_form_data(data)
                    
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
                    return self._fill_supplier_order_overlay(template_path, data, output_path)
                    
        except Exception as e:
            raise PDFFillError(f"Failed to fill supplier order PDF with PyPDF2: {str(e)}")
        
        return output_path
    
    def _fill_supplier_order_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill supplier order PDF by creating an overlay with positioned text."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            # Fallback to simple copy with a warning
            shutil.copy2(template_path, output_path)
            print(f"Warning: PyPDF2 not available. Template copied to: {output_path}")
            return output_path
        
        try:
            # Create overlay with text
            overlay_path = self._create_supplier_order_overlay(data)
            
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
            raise PDFFillError(f"Failed to create supplier order PDF overlay: {str(e)}")
        
        return output_path
    
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

                {"field": "client_company", "x": 60, "y": 185},
                {"field": "client_email", "x": 60, "y": 200},
                {"field": "client_phone", "x": 60, "y": 215},
                {"field": "client_address", "x": 60, "y": 230},
                

             {"field": "devie_number", "x": 515, "y": 139},
                {"field": "devie_date", "x": 500, "y": 153}
            ]

            for item in coordinates:
                field_name = item["field"]
                if field_name in field_map:
                    # Set different font styles for different fields
                    if field_name == "client_company":
                        c.setFont("Helvetica-Bold", 16)  # Bigger and bold for company name
                    elif field_name in ["client_email", "client_address", "client_phone"]:
                        c.setFont("Helvetica", 11)  # Smaller font size for contact details
                    else:
                        c.setFont("Helvetica", 10)  # Normal font size for other fields
                    
                    c.drawString(item["x"], height - item["y"], str(field_map[field_name]))

            # Line items table
            if 'line_items' in data:
                is_initial = data.get('is_initial', False)
                
                if is_initial:
                    table_data = [["Description", "Dimensions", "Couleur", "Cliché", "Quantité Min.", "UTTC"]]
                else:
                    table_data = [["Description", "Dimensions", "Couleur", "Cliché", "Qté", "UTTC"]]
                
                for item in data['line_items']:
                    # Extract numeric quantity for calculations
                    import re
                    quantity_str = str(item.get('quantity', '0'))
                    numbers = re.findall(r'\d+', quantity_str)
                    numeric_quantity = int(numbers[-1]) if numbers else 0
                    
                    cliche_status = "Oui" if item.get('is_cliche') else "Non"
                    
                    # Get dimensions from the item data
                    dimensions = item.get('dimensions', '')
                    if not dimensions and item.get('length_mm') and item.get('width_mm') and item.get('height_mm'):
                        # Fallback: calculate if not provided
                        dimensions = f"{item['length_mm']} × {item['width_mm']} × {item['height_mm']}"
                    
                    table_data.append([
                        str(item.get('description', '')),
                        dimensions,
                        str(item.get('color', '')),
                        cliche_status,
                        str(item.get('quantity', '')),  # Display original quantity string
                        f"{item.get('unit_price', 0):.2f}"
                    ])

                # Create and style the table
                if is_initial:
                    # Column widths for initial devis: Description, Dimensions, Couleur, Cliché, Quantité Min., UTTC
                    table = Table(table_data, colWidths=[110, 100, 45, 45, 85, 45])
                else:
                    # Column widths for regular devis: Description, Dimensions, Couleur, Cliché, Qté, UTTC
                    table = Table(table_data, colWidths=[120, 110, 50, 50, 75, 50])
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#BBDEFB")]),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True)
                ])

                table.setStyle(style)

                # Center the table horizontally on the page
                table_width, table_height = table.wrap(0, 0)
                x_position = (width - table_width) / 2  # Center X
                desired_y_top = 540
                y_position = desired_y_top - table_height  
                table.wrapOn(c, width, height)
                table.drawOn(c, x_position, y_position)

                # Note for initial devis
                if data.get('is_initial', False):
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
    
    def _create_supplier_order_overlay(self, data: Dict[str, Any]) -> str:
        """Create a transparent PDF overlay with positioned text for supplier orders."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        
        try:
            c = canvas.Canvas(temp_path, pagesize=A4)
            width, height = A4
            
            # Add title "Bon de commande"
            c.setFont("Helvetica-Bold", 20)
            title_text = "Bon de commande"
            title_width = c.stringWidth(title_text, "Helvetica-Bold", 20)
            c.drawString((width - title_width) / 2, height - 150, title_text)
            # Add confirmation text above the table
            c.setFont("Helvetica", 11)
            confirmation_text = "    Nous confirmons par la présente notre commande des plaques, selon les spécifications détaillées ci-après."

            # Split text into lines if too long
            text_width = c.stringWidth(confirmation_text, "Helvetica", 11)
            if text_width > width - 90:  # If text is too wide, split it
                words = confirmation_text.split()
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if c.stringWidth(test_line, "Helvetica", 11) <= width - 100:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                
                # Draw each line
                y_pos = height - 250
                for line in lines:
                    c.drawString(50, y_pos, line)
                    y_pos -= 15
            else:
                # Single line
                c.drawString(50, height - 250, confirmation_text)
            # Set font
            c.setFont("Helvetica", 10)
            
            # Position text fields for supplier order template (page.pdf)
            field_map = {
                "order_reference": f"N° : {data.get('reference', '')}",
                "order_date": f"Date : {data.get('order_date', '')}",
                "supplier_name": data.get('supplier_name', ''),
                "supplier_contact": data.get('supplier_contact', ''),
                "supplier_email": data.get('supplier_email', ''),
                "supplier_phone": data.get('supplier_phone', ''),
            }

            # Coordinates for supplier order fields (adjust based on page.pdf template)
            # Pour: (Supplier Information)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 165, "Pour:")
            
            coordinates = [
                {"field": "order_reference", "x": 450, "y": 165},
                {"field": "order_date", "x": 450, "y": 175},


                {"field": "supplier_name", "x": 75, "y": 180},
                {"field": "supplier_email", "x": 75, "y": 195},
                {"field": "supplier_phone", "x": 75, "y": 210}
            ]

            for item in coordinates:
                field_name = item["field"]
                if field_name in field_map and field_map[field_name]:
                    # Set font styles for different fields
                    if field_name == "supplier_name":
                        c.setFont("Helvetica-Bold", 14)
                    elif field_name == "order_reference":
                        c.setFont("Helvetica-Bold", 12)
                    else:
                        c.setFont("Helvetica", 10)
                    
                    c.drawString(item["x"], height - item["y"], str(field_map[field_name]))

            # Order items table
            if 'order_items' in data and data['order_items']:
                
                table_data = [["N°", "R°", "Mesure", "Désignation", "Caractéristique", "Prix UTTC", "Quantité"]]
                
                for idx, item in enumerate(data['order_items'], 1):
                    # Build mesure de caisse string (box dimensions)
                    mesure_caisse = ""
                    if item.get('length_mm') and item.get('width_mm') and item.get('height_mm'):
                        mesure_caisse = f"{item['length_mm']} / {item['width_mm']} / {item['height_mm']}"
                    
                    # Build designation de plaque string (plaque dimensions)
                    designation_plaque = ""
                    if item.get('plaque_width_mm') and item.get('plaque_length_mm') and item.get('plaque_flap_mm'):
                        designation_plaque = f"{item['plaque_width_mm']} / {item['plaque_length_mm']} / {item['plaque_flap_mm']}"
                    else:
                        # Fallback if plaque dimensions not available
                        designation_plaque = "À définir"
                    
                    # Get plaque characteristics
                    caracteristique = item.get('grammage', '') or item.get('cardboard_type', '') or "Standard"
                    
                    # Get reference de matière première (same as chosen in devis)
                    ref_matiere = item.get('material_reference', '') or item.get('reference', '') or ""
                    
                    # Get unit price
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    
                    table_data.append([
                        str(idx),
                        ref_matiere,
                        mesure_caisse,
                        designation_plaque,
                        caracteristique,
                        f"{unit_price:.2f}",
                        str(item.get('estimated_quantity', ''))
                    ])

                # Create and style the table with improved column widths for better text display
                # Adjusted column widths to better accommodate longer text
                table = Table(table_data, colWidths=[25, 70, 100, 100, 80, 65, 55])
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 1), (-1, -1), 8),  # Increased padding for better text display
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),  # Increased padding for better text display
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#BBDEFB")]),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrapping
                    ('SPLITLONGWORDS', (0, 0), (-1, -1), True),  # Split long words if necessary
                ])

                table.setStyle(style)

                # Position the table
                table_width, table_height = table.wrap(0, 0)
                x_position = (width - table_width) / 2
                desired_y_top = 550 
                y_position = desired_y_top - table_height  

                table.wrapOn(c, width, height)
                table.drawOn(c, x_position, y_position)

            # Add signature section in the right corner
            c.setFont("Helvetica-Bold", 10)  # Set to bold for "Signateur"
            signature_x = width - 200  # Right side positioning
            signature_y = 200  # Bottom area
            
            # Get current date
            from datetime import date
            current_date = date.today().strftime('%d/%m/%Y')
            
            c.drawString(signature_x, signature_y, "Signateur :")
            
            # Switch back to normal font for the date line
            c.setFont("Helvetica", 8)
            c.drawString(signature_x, signature_y - 20, f"Fait le {current_date} à BEJAIA")
            
            # Add a line for signature
            c.line(signature_x, signature_y - 100, signature_x + 150, signature_y - 100)

            c.showPage()
            c.save()
        except Exception as e:
            raise PDFFillError(f"Failed to create supplier order overlay: {str(e)}")
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
    
    def _prepare_supplier_order_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare data for supplier order PDF form fields."""
        form_data = {}
        
        # Map data to common form field names for supplier orders
        field_mappings = {
            'reference': ['reference', 'ref', 'numero', 'order_number'],
            'supplier_name': ['supplier', 'supplier_name', 'vendor'],
            'order_date': ['date', 'order_date', 'date_commande'],
            'expected_delivery_date': ['delivery_date', 'expected_delivery', 'livraison'],
            'total_amount': ['total', 'total_amount', 'amount'],
            'notes': ['notes', 'remarks', 'comments']
        }
        
        for data_key, form_fields in field_mappings.items():
            if data_key in data:
                value = str(data[data_key])
                for field_name in form_fields:
                    form_data[field_name] = value
        
        return form_data

    def fill_finished_product_template(self, product_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the finished product fiche PDF template (PF.pdf) with product data.
        
        Args:
            product_data: Dictionary containing finished product information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "PF.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            client = product_data.get('client', 'client')
            timestamp = date.today().strftime('%Y%m%d_%H%M%S')
            quantity = product_data.get('quantity', '0')
            output_filename = f"fiche_produit_fini_{client}_{quantity}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_finished_product_pypdf(template_path, product_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_finished_product_overlay(template_path, product_data, output_path)
    
    def _fill_finished_product_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill finished product PDF using PyPDF2 form fields."""
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
                    field_data = self._prepare_finished_product_form_data(data)
                    
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    
                    pdf_writer.update_page_form_field_values(pdf_writer.pages[0], field_data)
                    
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                else:
                    # No form fields, use overlay method
                    return self._fill_finished_product_overlay(template_path, data, output_path)
                
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error filling finished product PDF: {e}")
    
    def _fill_finished_product_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill finished product PDF using overlay method."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            raise PDFFillError("PyPDF2 not available for overlay method")
        
        try:
            # Create overlay with text
            overlay_path = self._create_finished_product_overlay(data)
            
            # Merge overlay with template
            with open(template_path, 'rb') as template_file, open(overlay_path, 'rb') as overlay_file:
                template_pdf = PyPDF2.PdfReader(template_file)
                overlay_pdf = PyPDF2.PdfReader(overlay_file)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                # Merge pages
                template_page = template_pdf.pages[0]
                overlay_page = overlay_pdf.pages[0]
                template_page.merge_page(overlay_page)
                pdf_writer.add_page(template_page)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            # Clean up temporary overlay file
            overlay_path.unlink()
            
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error creating finished product PDF overlay: {e}")
    
    def _prepare_finished_product_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare form field data for finished product template."""
        return {
            'date_production': str(data.get('production_date', '')),
            'client': str(data.get('client', '')),
            'quantite': str(data.get('quantity', '')),
            # Map both dimensions and designation (description from devis);
            # many templates label the text box as 'dimensions'. We'll prefer designation if available
            'dimensions': str(data.get('designation') or data.get('dimensions', '')),
            'designation': str(data.get('designation', '')),
            'reference': str(data.get('reference', ''))
        }
    
    def _create_finished_product_overlay(self, data: Dict[str, Any]) -> Path:
        """Create a text overlay for finished product data."""
        overlay_path = Path(tempfile.mktemp(suffix='.pdf'))
        
        # Create PDF with text at specific positions
        c = canvas.Canvas(str(overlay_path), pagesize=A4)
        width, height = A4
        
        # Set font
        c.setFont("Helvetica-Bold", 15)
        
        # Add text at approximate positions (adjust as needed based on template)
        # Reference (top of document)
        reference = data.get('reference', '')
        c.drawString(447.67, 272.58, str(reference))
        
        # Date de production
        production_date = data.get('production_date', '')
        c.drawString(314.93, 433.70, str(production_date))
        
        # Client
        client = data.get('client', '')
        c.drawString(142.82, 376.03, str(client))
        
    
        # Quantité
        quantity = data.get('quantity', '')
        c.drawString(160.21, 271.66, f"{quantity} caisses")
        
        # Dimensions (keep original dimensions field for form compatibility)
        dimensions = data.get('dimensions', '')
        c.drawString(256.34, 219.48, str(dimensions))
        
        c.save()
        return overlay_path

    def fill_raw_material_label_template(self, label_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the raw material label PDF template (MP.pdf) with label data.
        
        Args:
            label_data: Dictionary containing raw material label information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "MP.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            client = label_data.get('client', 'client')
            timestamp = date.today().strftime('%Y%m%d_%H%M%S')
            label_number = label_data.get('label_number', '000')
            output_filename = f"etiquette_mp_{client}_{label_number}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_raw_material_label_pypdf(template_path, label_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_raw_material_label_overlay(template_path, label_data, output_path)
    
    def _fill_raw_material_label_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill raw material label PDF using PyPDF2 form fields."""
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
                    field_data = self._prepare_raw_material_label_form_data(data)
                    
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    
                    pdf_writer.update_page_form_field_values(pdf_writer.pages[0], field_data)
                    
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                else:
                    # No form fields, use overlay method
                    return self._fill_raw_material_label_overlay(template_path, data, output_path)
                
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error filling raw material label PDF: {e}")
    
    def _fill_raw_material_label_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill raw material label PDF using overlay method."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            raise PDFFillError("PyPDF2 not available for overlay method")
        
        try:
            # Create overlay with text
            overlay_path = self._create_raw_material_label_overlay(data)
            
            # Merge overlay with template
            with open(template_path, 'rb') as template_file, open(overlay_path, 'rb') as overlay_file:
                template_pdf = PyPDF2.PdfReader(template_file)
                overlay_pdf = PyPDF2.PdfReader(overlay_file)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                # Merge pages
                template_page = template_pdf.pages[0]
                overlay_page = overlay_pdf.pages[0]
                template_page.merge_page(overlay_page)
                pdf_writer.add_page(template_page)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            # Clean up temporary overlay file
            overlay_path.unlink()
            
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error creating raw material label PDF overlay: {e}")
    
    def _prepare_raw_material_label_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare form field data for raw material label template."""
        return {
            'derniere_date_arrivee': str(data.get('arrival_date', '')),
            'client': str(data.get('client', '')),
            'quantite': str(data.get('quantity', '')),
            'numero_etiquette': str(data.get('label_number', '')),
            'dimension_plaque': str(data.get('plaque_dimensions', '')),
            'dimension_caisse': str(data.get('caisse_dimensions', '')),
            'cliche': str(data.get('cliche', 'Non')),
            'remarque': str(data.get('remark', '')),
            'numero_bon_commande': str(data.get('bon_commande', '')),
            'reste': str(data.get('remaining_quantity', ''))
        }
    
    def _create_raw_material_label_overlay(self, data: Dict[str, Any]) -> Path:
        """Create a text overlay for raw material label data."""
        overlay_path = Path(tempfile.mktemp(suffix='.pdf'))
        
        # Create PDF with text at specific positions
        c = canvas.Canvas(str(overlay_path), pagesize=A4)
        width, height = A4
        
        # Set font
        c.setFont("Helvetica", 10)
        
        # Add text at approximate positions (adjust as needed based on template)
        # Dernière date d'arrivée
        arrival_date = data.get('arrival_date', '')
        c.setFont("Helvetica", 15) 
        c.drawString(264.58, 474.90, str(arrival_date))
        
        # Client
        client = data.get('client', '')
        c.setFont("Helvetica-Bold", 15) 
        c.drawString(143.33, 423.67, str(client))

        
        # Quantité
        quantity = data.get('quantity', '')
        c.setFont("Helvetica-Bold", 15)
        c.drawString(160.21, 325.67, f"{quantity} plaques")
        
        # N° étiquette
        label_number = data.get('label_number', '')
        c.drawString( 444.93, 325.67, str(label_number))

    
        # Dimension plaque
        plaque_dimensions = data.get('plaque_dimensions', '')
        c.setFont("Helvetica-Bold", 15)
        c.drawString(240.77, 271.66, str(plaque_dimensions))
        
        # Dimension caisse
        caisse_dimensions = data.get('caisse_dimensions', '')
        c.setFont("Helvetica-Bold", 15)
        c.drawString(240.77, 217.65, str(caisse_dimensions))
        
        # Cliché
        cliche = data.get('cliche', 'Non')
        c.setFont("Helvetica-Bold", 15)
        c.drawString(148.31, 146.24, str(cliche))
        
        # Remarque
        remark = data.get('remark', '')
        c.setFont("Helvetica-Bold", 15)
        c.drawString(356.13, 146.24, str(remark))
        
        # Numéro de Bon de commande
        bon_commande = data.get('bon_commande', '')
        c.drawString(234.37, 94.06, str(bon_commande))
        
        # Resté
        remaining = data.get('remaining_quantity', '')
        c.drawString(355.21, 94.06, str(remaining))
        
        c.save()
        return overlay_path

    def fill_invoice_template(self, invoice_data: Dict[str, Any], output_filename: str | None = None) -> Path:
        """
        Fill the invoice PDF template (page.pdf) with invoice data.
        
        Args:
            invoice_data: Dictionary containing invoice information
            output_filename: Optional custom filename for output
            
        Returns:
            Path to the generated PDF file
        """
        template_path = self.template_dir / "page.pdf"
        
        if not template_path.exists():
            raise PDFFillError(f"Template not found: {template_path}")
        
        # Generate output filename if not provided
        if not output_filename:
            invoice_number = invoice_data.get('invoice_number', 'FACT')
            timestamp = date.today().strftime('%Y%m%d')
            output_filename = f"facture_{invoice_number}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to use PyPDF2 for form filling if available
        if self._ensure_pypdf_installed():
            return self._fill_invoice_pypdf(template_path, invoice_data, output_path)
        else:
            # Fallback to overlay method
            return self._fill_invoice_overlay(template_path, invoice_data, output_path)
    
    def _fill_invoice_pypdf(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill invoice PDF using PyPDF2 form fields."""
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
                    field_data = self._prepare_invoice_form_data(data)
                    
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    
                    pdf_writer.update_page_form_field_values(pdf_writer.pages[0], field_data)
                    
                    with open(output_path, 'wb') as output_file:
                        pdf_writer.write(output_file)
                else:
                    # No form fields, use overlay method
                    return self._fill_invoice_overlay(template_path, data, output_path)
                
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error filling invoice PDF: {e}")
    
    def _fill_invoice_overlay(self, template_path: Path, data: Dict[str, Any], output_path: Path) -> Path:
        """Fill invoice PDF using overlay method."""
        try:
            import PyPDF2  # type: ignore
        except ImportError:
            raise PDFFillError("PyPDF2 not available for overlay method")
        
        try:
            # Create overlay with text
            overlay_path = self._create_invoice_overlay(data)
            
            # Merge overlay with template
            with open(template_path, 'rb') as template_file, open(overlay_path, 'rb') as overlay_file:
                template_pdf = PyPDF2.PdfReader(template_file)
                overlay_pdf = PyPDF2.PdfReader(overlay_file)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                # Merge pages
                template_page = template_pdf.pages[0]
                overlay_page = overlay_pdf.pages[0]
                template_page.merge_page(overlay_page)
                pdf_writer.add_page(template_page)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
            
            # Clean up temporary overlay file
            overlay_path.unlink()
            
            return output_path
        except Exception as e:
            raise PDFFillError(f"Error creating invoice PDF overlay: {e}")
    
    def _prepare_invoice_form_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare form field data for invoice template."""
        return {
            'numero_facture': str(data.get('invoice_number', '')),
            'date_facture': str(data.get('invoice_date', '')),
            'client_nom': str(data.get('client_name', '')),
            'client_activite': str(data.get('client_activity', '')),
            'client_adresse': str(data.get('client_address', '')),
            'client_rc': str(data.get('client_rc', '')),
            'client_nif': str(data.get('client_nif', '')),
            'client_nis': str(data.get('client_nis', '')),
            'client_ai': str(data.get('client_ai', '')),
            'client_telephone': str(data.get('client_phone', '')),
            'mode_paiement': str(data.get('payment_mode', '')),
            'total_ht_brut': str(data.get('total_ht', '')),
            'remise': str(data.get('discount', '0%')),
            'total_ht_net': str(data.get('total_ht_net', '')),
            'tva': str(data.get('tva', '')),
            'total_ttc': str(data.get('total_ttc', '')),
            'timbre': str(data.get('timbre', '0')),
            'total_ttc_net': str(data.get('total_ttc_net', '')),
            'montant_lettres': str(data.get('amount_in_words', '')),
            'date_signature': str(data.get('signature_date', ''))
        }
    
    def _create_invoice_overlay(self, data: Dict[str, Any]) -> Path:
        """Create a text overlay for invoice data with professional styling."""
        overlay_path = Path(tempfile.mktemp(suffix='.pdf'))
        
        # Create PDF with text at specific positions
        c = canvas.Canvas(str(overlay_path), pagesize=A4)
        width, height = A4
        
        # Define night blue color
        night_blue = colors.HexColor("#1B4A7F")
        
        # Title "FACTURE" - bold, night blue, centered
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(night_blue)
        title_text = "FACTURE"
     
        c.drawString(70, 690, title_text)
        
        # Invoice number and date - aligned left under title
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        invoice_number = data.get('invoice_number', '')

        c.drawString(70, 675, f"N°: {invoice_number}")

        # Client information (aligned right) using Paragraph with automatic wrapping and vertical flow
        c.setFont("Helvetica", 10)

        # Helper to draw a paragraph and return vertical advance (height + spacing)
        def draw_paragraph_advance(
            text: str,
            x: float,
            y: float,
            *,
            max_width: float = 240.0,
            font_name: str = "Helvetica",
            font_size: int = 10,
            leading: int | None = None,
            spacing: float = 0.0,
        ) -> float:
            if not text:
                return 0.0
            style = ParagraphStyle(
                name='ClientInfo',
                fontName=font_name,
                fontSize=font_size,
                leading=(leading if leading is not None else font_size + 2),
            )
            p = Paragraph(text, style)
            _w, h = p.wrap(max_width, 1000)  # large available height
            p.drawOn(c, x, y - h)
            return h + spacing

        # Start at the top-most Y used previously and flow down
        current_y = 703
        current_y -= draw_paragraph_advance(
            f"<b>Nom ou Raison Sociale :</b> {data.get('client_name', '')}", 350, current_y
        )

        client_activity = data.get('client_activity', '')
        if client_activity:
            current_y -= draw_paragraph_advance(f"<b>Activité :</b> {str(client_activity)}", 350, current_y)
        
        client_address = data.get('client_address', '')
        if client_address:
            current_y -= draw_paragraph_advance(f"<b>Adresse :</b> {str(client_address)}", 350, current_y)
        
        # RC, NIF, NIS, AI fields
        client_rc = data.get('client_rc', '')
        if client_rc:
            current_y -= draw_paragraph_advance(f"<b>N°RC:</b> {client_rc}", 350, current_y)
        
        client_nif = data.get('client_nif', '')
        if client_nif:
            current_y -= draw_paragraph_advance(f"<b>NIF:</b> {client_nif}", 350, current_y)
        
        client_nis = data.get('client_nis', '')
        if client_nis:
            current_y -= draw_paragraph_advance(f"<b>NIS:</b> {client_nis}", 350, current_y)

        client_ai = data.get('client_ai', '')
        if client_ai:
            current_y -= draw_paragraph_advance(f"<b>A.I:</b> {client_ai}", 350, current_y)

        client_phone = data.get('client_phone', '')
        if client_phone:
            current_y -= draw_paragraph_advance(f"<b>Tél:</b> {client_phone}", 350, current_y)

        # Payment mode (wrapped and placed after client info block without overlap)
        c.setFont("Helvetica", 10)
        payment_mode = data.get('payment_mode', 'Mode de Paiement: …')
        y_payment_top = min(current_y, 634)
        pay_style = ParagraphStyle(name='Payment', fontName='Helvetica', fontSize=10, leading=12)
        pay_para = Paragraph(f"Mode de Paiement: {payment_mode}", pay_style)
        _w, _h = pay_para.wrap(300, 1000)
        pay_para.drawOn(c, 70, y_payment_top - _h)
        current_y = y_payment_top - _h

        # Table section - Invoice items table
        footer_anchor_y = None  # will capture the Y of the 'Total TTC NET' line for footer spacing
        if 'line_items' in data and data['line_items']:
            include_tva = bool(data.get('include_tva', True))
            if include_tva:
                table_data = [["N°", "Designation", "QTE", "P/U HT", "TVA", "Total HT"]]
            else:
                table_data = [["N°", "Designation", "QTE", "P/U HT", "Total HT"]]
            
            total_ht = Decimal('0')
            for idx, item in enumerate(data['line_items'], 1):
                unit_price = Decimal(str(item.get('unit_price', 0)))
                quantity = int(item.get('quantity', 0))
                line_total = unit_price * quantity
                tva_rate = item.get('tva_rate', 19)
                if include_tva:
                    table_data.append([
                        str(idx),
                        str(item.get('designation', '')),
                        str(quantity),
                        f"{unit_price:.2f}",
                        f"{tva_rate}%",
                        f"{line_total:.2f} DA"
                    ])
                else:
                    table_data.append([
                        str(idx),
                        str(item.get('designation', '')),
                        str(quantity),
                        f"{unit_price:.2f}",
                        f"{line_total:.2f} DA"
                    ])
                total_ht += line_total
            
            # Create and style the table with professional borders
            # Choose column widths depending on TVA column presence
            if include_tva:
                table = Table(table_data, colWidths=[30, 200, 50, 70, 50, 95])
            else:
                table = Table(table_data, colWidths=[30, 220, 60, 80, 110])
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), night_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
                ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
            ])
            
            table.setStyle(style)
            
            # Position the table; ensure it does not overlap header/client/payment block
            table_width, table_height = table.wrap(0, 0)
            x_position = (width - table_width) / 2
            desired_margin_top = 250
            default_y_top = height - desired_margin_top
            safe_y_top = min(default_y_top, current_y - 20)
            y_position = safe_y_top - table_height
            table.drawOn(c, x_position, y_position)

            
            # Summary section (aligned right, under table)
            # Requirements:
            # - Distance from end of the table to first summary line: 20pt
            # - Distance between each summary line: 16pt
            summary_x = width - 200
            line_spacing = 16
            summary_y = y_position - 20
            
            c.setFont("Helvetica", 10)
            total_ht_brut = data.get('total_ht', total_ht)
            c.drawString(summary_x, summary_y, f"Total HT Brut: {total_ht_brut:.2f} DA")
            
            discount = data.get('discount', '0%')
            c.drawString(summary_x, summary_y - line_spacing, f"Remise: {discount}")
            
            total_ht_net = data.get('total_ht_net', total_ht_brut)
            c.drawString(summary_x, summary_y - (2 * line_spacing), f"Total HT Net: {total_ht_net:.2f} DA")
            
            tva_amount = data.get('tva_amount', total_ht_net * Decimal('0.19'))
            tva_label = data.get('tva_label', 'TVA (19%)')
            curr_y = summary_y - (3 * line_spacing)
            if include_tva:
                c.drawString(summary_x, curr_y, f"{tva_label}: {tva_amount:.2f} DA")
                curr_y -= line_spacing
                total_ttc = data.get('total_ttc', total_ht_net + tva_amount)
                c.drawString(summary_x, curr_y, f"Total TTC: {total_ttc:.2f} DA")
                curr_y -= line_spacing
                timbre = data.get('timbre', 0)
                try:
                    timbre_val = Decimal(str(timbre))
                except Exception:
                    timbre_val = Decimal('0')
                c.drawString(summary_x, curr_y, f"TIMBRE 1%: {timbre_val:.2f} DA")
                curr_y -= line_spacing
            else:
                # Without TVA, skip TVA and TIMBRE rows entirely and compute TTC inline
                total_ttc = data.get('total_ttc', total_ht_net)
                c.drawString(summary_x, curr_y, f"Total TTC: {total_ttc:.2f} DA")
                curr_y -= line_spacing

            # Total TTC NET - bold, night blue highlight, spaced by 12pt from previous line
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(night_blue)
            total_ttc_net = data.get('total_ttc_net', total_ttc)
            c.drawString(summary_x, curr_y, f"Total TTC NET: {total_ttc_net:.2f} DA")
            # Capture anchor for footer placement (first footer line will be 50pt below this)
            footer_anchor_y = curr_y
            
            # Reset color for footer
            c.setFillColor(colors.black)
        
        # Footer section
        # Amount in words - sentence in red
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.red)
        amount_in_words = data.get('amount_in_words', '')
        last_amount_line_y = None  # track the Y of the last red line
        if amount_in_words:
            # Split long text into multiple lines
            max_width = width - 100
            words = amount_in_words.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            # Draw each line, with the first line exactly 50pt below the 'Total TTC NET' line if available
            if footer_anchor_y is not None:
                footer_y = max(50, footer_anchor_y - 50)  # keep above bottom margin
            else:
                footer_y = 150
            for line in lines:
                c.drawString(50, footer_y, line)
                last_amount_line_y = footer_y
                footer_y -= 15
        
        # Signature placeholder bottom right
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        signature_x = width - 200
        # If we drew the amount-in-words, place signature exactly 50pt below the last red line
        if last_amount_line_y is not None:
            signature_y = max(50, last_amount_line_y - 50)  # keep a small bottom margin
        else:
            signature_y = 80
        
        c.drawString(signature_x, signature_y, "SIGNATURE:")
        
        signature_date = data.get('signature_date', date.today().strftime('%d/%m/%Y'))
        c.drawString(signature_x, signature_y - 20, f"Bejaia le: {signature_date}")
        
        c.save()
        return overlay_path


__all__ = ['PDFFormFiller', 'PDFFillError']
