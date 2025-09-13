#!/usr/bin/env python3
"""
Test script to verify the new Archive interface functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_archive_widget_import():
    """Test that the archive widget can be imported successfully"""
    try:
        from ui.widgets.archive_widget import ArchiveWidget, ArchiveStatsWidget, ArchiveTableWidget
        print("✅ Successfully imported all archive widget classes")
        return True
    except Exception as e:
        print(f"❌ Error importing archive widgets: {e}")
        return False

def test_archive_widget_creation():
    """Test creating archive widget instances"""
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        
        # Test creating widgets
        from ui.widgets.archive_widget import ArchiveWidget, ArchiveStatsWidget, ArchiveTableWidget
        
        stats_widget = ArchiveStatsWidget()
        print("✅ Successfully created ArchiveStatsWidget")
        
        table_widget = ArchiveTableWidget(["Test", "Headers"])
        print("✅ Successfully created ArchiveTableWidget")
        
        archive_widget = ArchiveWidget()
        print("✅ Successfully created main ArchiveWidget")
        
        # Test that the widget has all expected components
        assert hasattr(archive_widget, 'stats_widget'), "Missing stats_widget"
        assert hasattr(archive_widget, 'tab_widget'), "Missing tab_widget"
        assert hasattr(archive_widget, 'quotations_table'), "Missing quotations_table"
        assert hasattr(archive_widget, 'client_orders_table'), "Missing client_orders_table"
        assert hasattr(archive_widget, 'production_table'), "Missing production_table"
        assert hasattr(archive_widget, 'supplier_orders_table'), "Missing supplier_orders_table"
        assert hasattr(archive_widget, 'timeline_table'), "Missing timeline_table"
        
        print("✅ All archive widget components present")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error creating archive widgets: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_archive_functionality():
    """Test key archive functionality"""
    try:
        from config.database import SessionLocal
        from models.production import ProductionBatch
        from models.orders import Quotation, ClientOrder, SupplierOrder
        
        session = SessionLocal()
        try:
            # Test archive filtering queries (should not crash)
            archived_quotations = session.query(Quotation).filter(
                Quotation.notes.like('[ARCHIVED]%')
            ).count()
            
            archived_production = session.query(ProductionBatch).filter(
                ProductionBatch.batch_code.like('[ARCHIVED]%')
            ).count()
            
            archived_client_orders = session.query(ClientOrder).filter(
                ClientOrder.notes.like('[ARCHIVED]%')
            ).count()
            
            archived_supplier_orders = session.query(SupplierOrder).filter(
                SupplierOrder.notes.like('[ARCHIVED]%')
            ).count()
            
            print(f"✅ Found {archived_quotations} archived quotations")
            print(f"✅ Found {archived_production} archived production batches")
            print(f"✅ Found {archived_client_orders} archived client orders")
            print(f"✅ Found {archived_supplier_orders} archived supplier orders")
            
            return True
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error testing archive functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔍 Testing World Embalage Archive Interface")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_archive_widget_import),
        ("Widget Creation Test", test_archive_widget_creation),
        ("Archive Functionality Test", test_archive_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        
    print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Archive interface is ready!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")