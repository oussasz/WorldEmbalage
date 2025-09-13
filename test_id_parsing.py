#!/usr/bin/env python3
"""
Simple test to verify the ID parsing logic works correctly.
"""

def test_id_parsing():
    """Test ID parsing logic for both old and new formats"""
    
    test_cases = [
        "1,2,3",      # New comma-separated format
        "5",          # Single ID
        "1-3 (3)",    # Old merged format
        "10,20,30,40", # Multiple comma-separated IDs
        "invalid",    # Invalid format
    ]
    
    print("🔍 Testing ID Parsing Logic")
    print("=" * 40)
    
    for test_id in test_cases:
        print(f"\nTesting: '{test_id}'")
        
        # Check if it's a comma-separated format (new grouping system)
        if ',' in test_id:
            ids_str = [id_str.strip() for id_str in test_id.split(',')]
            try:
                batch_ids = [int(id_str) for id_str in ids_str]
                print(f"   ✅ Comma-separated format: {batch_ids}")
            except ValueError:
                print(f"   ❌ Invalid comma-separated format")
            continue
        
        # Check if it's the old merged format
        import re
        if re.match(r'^\d+-\d+ \(\d+\)$', test_id):
            range_match = re.match(r'^(\d+)-(\d+) \((\d+)\)$', test_id)
            if range_match:
                start_id = int(range_match.group(1))
                end_id = int(range_match.group(2))
                batch_ids = list(range(start_id, end_id + 1))
                count = int(range_match.group(3))
                print(f"   ✅ Old merged format: {batch_ids} (count: {count})")
            continue
        
        # Single item
        if test_id.isdigit():
            production_id = int(test_id)
            print(f"   ✅ Single ID: {production_id}")
        else:
            print(f"   ❌ Invalid ID format")

if __name__ == "__main__":
    test_id_parsing()
