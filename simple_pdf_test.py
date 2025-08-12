#!/usr/bin/env python3
"""
Simple PDF creation test - create a sample PDF without database dependencies.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from services.pdf_form_filler import PDFFormFiller, PDFFillError

def test_sample_pdf():
    """Test PDF generation with sample data."""
    # Sample quotation data
    sample_data = {
        'reference': 'DEV-2024-001-TEST',
        'issue_date': '2024-12-08',
        'valid_until': '2024-12-31',
        'client_name': 'Test Client SARL',
        'client_address': '123 Rue Test, Alger, Algérie',
        'client_phone': '+213 21 123 456',
        'client_email': 'test@client.dz',
        'line_items': [
            {
                'description': 'Carton simple cannelure 30x20x15',
                'quantity': 100,
                'unit_price': 45.50,
                'total_price': 4550.00,
                'dimensions': '300 x 200 x 150 mm',
                'color': 'brun',
                'cardboard_type': 'Simple cannelure'
            },
            {
                'description': 'Carton double cannelure 40x30x20',
                'quantity': 50,
                'unit_price': 85.00,
                'total_price': 4250.00,
                'dimensions': '400 x 300 x 200 mm',
                'color': 'blanc',
                'cardboard_type': 'Double cannelure'
            }
        ],
        'total_amount': 8800.00,
        'notes': 'Livraison sous 15 jours. Paiement à 30 jours.',
        'currency': 'DZD'
    }
    
    print("Sample quotation data:")
    print(f"  Reference: {sample_data['reference']}")
    print(f"  Client: {sample_data['client_name']}")
    print(f"  Items: {len(sample_data['line_items'])}")
    print(f"  Total: {sample_data['total_amount']} {sample_data['currency']}")
    
    # Generate PDF using template
    pdf_filler = PDFFormFiller()
    try:
        output_path = pdf_filler.fill_devis_template(sample_data, "sample_devis_test.pdf")
        
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("World Embalage - Simple PDF Generation Test")
    print("=" * 45)
    
    success = test_sample_pdf()
    
    if success:
        print("\n🎉 PDF generation test completed successfully!")
        print("You can now test the print feature in the application by:")
        print("1. Right-clicking on a quotation in the orders grid")
        print("2. Selecting '🖨️ Imprimer devis' from the context menu")
    else:
        print("\n💥 PDF generation test failed!")
    
    sys.exit(0 if success else 1)
