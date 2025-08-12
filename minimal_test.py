#!/usr/bin/env python3
"""
Minimal PDF test to debug the issue.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def minimal_test():
    try:
        print("1. Testing imports...")
        from services.pdf_form_filler import PDFFormFiller, PDFFillError
        print("   ✓ PDFFormFiller imported successfully")
        
        print("2. Creating PDFFormFiller instance...")
        pdf_filler = PDFFormFiller()
        print(f"   ✓ Template dir: {pdf_filler.template_dir}")
        print(f"   ✓ Output dir: {pdf_filler.output_dir}")
        
        print("3. Checking template file...")
        template_path = pdf_filler.template_dir / "Devie.pdf"
        print(f"   Template path: {template_path}")
        print(f"   Template exists: {template_path.exists()}")
        
        if not template_path.exists():
            print("   ❌ Template file not found!")
            return False
        
        print("4. Testing PyPDF2 availability...")
        if pdf_filler._ensure_pypdf_installed():
            print("   ✓ PyPDF2 is available")
        else:
            print("   ⚠️ PyPDF2 not available, will use fallback")
        
        print("5. All tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Minimal PDF Form Filler Test")
    print("=" * 30)
    
    success = minimal_test()
    sys.exit(0 if success else 1)
