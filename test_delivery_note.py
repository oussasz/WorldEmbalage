#!/usr/bin/env python3
"""
Simple test for delivery note generation
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from reports.templates.delivery_note import build_delivery_note_pdf
from utils.reference_generator import generate_delivery_reference
from datetime import date

def test_delivery_note():
    """Test delivery note generation with sample data"""
    try:
        # Generate reference
        reference = generate_delivery_reference()
        print(f"Generated reference: {reference}")
        
        # Sample data
        client_name = "Test Client"
        client_details = """Test Client SARL
Contact: M. Jean Dupont
123 Rue de la Paix
06000 Bejaia
Algérie
Tél: +213 123 456 789
Email: contact@testclient.dz"""
        
        delivery_date = date.today()
        
        lines = [
            {
                'designation': 'Caisse Type A',
                'dimensions': '300 x 200 x 150 mm',
                'quantity': '1000'
            },
            {
                'designation': 'Caisse Type B',
                'dimensions': '400 x 300 x 200 mm', 
                'quantity': '500'
            }
        ]
        
        # Generate PDF
        pdf_path = build_delivery_note_pdf(
            reference=reference,
            client_name=client_name,
            delivery_date=delivery_date,
            lines=lines,
            client_details=client_details
        )
        
        print(f"✅ Delivery note generated successfully: {pdf_path}")
        print(f"File exists: {pdf_path.exists()}")
        print(f"File size: {pdf_path.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating delivery note: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_delivery_note()
