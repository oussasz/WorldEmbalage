#!/usr/bin/env python3
"""
Test script for PDF form filling functionality.
This script will test the PDF generation without needing to use the GUI.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import all models to avoid circular import issues
from models import *  # Import all models first
from config.database import SessionLocal
from services.order_service import OrderService
from services.pdf_form_filler import PDFFormFiller, PDFFillError
from models.orders import Quotation


def test_pdf_generation():
    """Test PDF generation for an existing quotation."""
    session = SessionLocal()
    try:
        # Find the first quotation in the database
        quotation = session.query(Quotation).first()
        
        if not quotation:
            print("No quotations found in database. Please create a quotation first.")
            return False
        
        print(f"Testing PDF generation for quotation: {quotation.reference}")
        
        # Get quotation data for PDF
        order_service = OrderService(session)
        quotation_data = order_service.get_quotation_for_pdf(quotation.id)
        
        print("Quotation data retrieved:")
        for key, value in quotation_data.items():
            if key == 'line_items':
                print(f"  {key}: {len(value)} items")
                for i, item in enumerate(value[:2]):  # Show first 2 items
                    print(f"    Item {i+1}: {item.get('description', 'N/A')} - {item.get('quantity', 0)} x {item.get('unit_price', 0)}")
            else:
                print(f"  {key}: {value}")
        
        # Generate PDF using template
        pdf_filler = PDFFormFiller()
        try:
            output_path = pdf_filler.fill_devis_template(quotation_data, f"test_devis_{quotation.reference}.pdf")
            
            if output_path.exists():
                print(f"\n✅ PDF generated successfully:")
                print(f"   File: {output_path.name}")
                print(f"   Location: {output_path.parent}")
                print(f"   Size: {output_path.stat().st_size} bytes")
                return True
            else:
                print("❌ PDF file was not created")
                return False
                
        except PDFFillError as e:
            print(f"❌ PDF generation error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("World Embalage - PDF Generation Test")
    print("=" * 40)
    
    success = test_pdf_generation()
    
    if success:
        print("\n🎉 PDF generation test completed successfully!")
    else:
        print("\n💥 PDF generation test failed!")
    
    sys.exit(0 if success else 1)
