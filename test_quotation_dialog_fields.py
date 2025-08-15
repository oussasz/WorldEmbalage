#!/usr/bin/env python3

"""Test script to verify quotation dialog field changes."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from ui.dialogs.quotation_dialog import QuotationDialog
from models.orders import Quotation


def test_quotation_dialog_fields():
    """Test that the quotation dialog has the correct number of columns and field names."""
    app = QApplication(sys.argv)
    
    # Create a dialog instance
    dialog = QuotationDialog()
    
    # Check table header count
    table = dialog.table
    column_count = table.columnCount()
    print(f"✓ Table has {column_count} columns (expected: 12)")
    assert column_count == 12, f"Expected 12 columns, got {column_count}"
    
    # Check specific header texts
    headers = []
    for i in range(column_count):
        item = table.horizontalHeaderItem(i)
        if item:
            headers.append(item.text())
        else:
            headers.append("")
    
    print("✓ Table headers:")
    for i, header in enumerate(headers):
        print(f"  {i}: {header}")
    
    # Verify specific renamed headers
    expected_headers = [
        "Description", "Quantité", "Prix unitaire HT", "Prix total HT",
        "Longueur (mm)", "Largeur (mm)", "Hauteur (mm)", "Couleur",
        "Caractéristique matière", "Référence matière première", "Cliché", "Notes"
    ]
    
    for i, expected in enumerate(expected_headers):
        actual = headers[i] if i < len(headers) else ""
        if expected in ["Caractéristique matière", "Référence matière première"]:
            if expected == "Caractéristique matière":
                print(f"✓ Header {i}: '{actual}' (renamed from 'Type carton')")
            elif expected == "Référence matière première":
                print(f"✓ Header {i}: '{actual}' (new field)")
        assert actual == expected, f"Column {i}: expected '{expected}', got '{actual}'"
    
    print("✓ All header checks passed!")
    
    # Test the get_data method structure
    dialog._add_item_row()
    data = dialog.get_data()
    
    # Verify data structure
    assert 'line_items' in data, "get_data should return line_items"
    if data['line_items']:
        line_item = data['line_items'][0]
        required_fields = [
            'description', 'quantity', 'unit_price', 'total_price',
            'length_mm', 'width_mm', 'height_mm', 'color',
            'cardboard_type', 'material_reference', 'is_cliche', 'notes'
        ]
        
        for field in required_fields:
            assert field in line_item, f"Line item missing field: {field}"
            if field == 'material_reference':
                print(f"✓ New field '{field}' present in data structure")
        
        print("✓ All required fields present in line item data")
    
    print("🎉 All tests passed! Quotation dialog fields are correctly configured.")
    app.quit()


if __name__ == "__main__":
    test_quotation_dialog_fields()
