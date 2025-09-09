# UNIFIED REFERENCE GENERATION SYSTEM

## Overview

The World Embalage application now uses a **unified reference generation system** that provides consistent, standardized reference formats across all document types. This eliminates the previous inconsistent reference formats and ensures all references follow a single, professional coding standard.

## New Standardized Format

All references now follow this format:

```
PREFIX-YYYYMMDD-HHMMSS-NNNN[-SUFFIX]
```

Where:

- **PREFIX**: Document type identifier (DEV, BC, CMD, FPF, MP, etc.)
- **YYYYMMDD**: Date (year-month-day)
- **HHMMSS**: Time (hour-minute-second)
- **NNNN**: Sequential number (4 digits, padded with zeros)
- **SUFFIX**: Optional custom suffix

### Examples

- Quotation: `DEV-20250902-143027-0001`
- Supplier Order: `BC-20250902-143027-0002`
- Client Order: `CMD-20250902-143027-0003`
- Finished Product: `FPF-20250902-143027-0001-COPIE001`
- Raw Material Label: `MP-20250902-143027-0001-1_2_3`

## Document Type Prefixes

| Document Type      | Prefix | Description                 |
| ------------------ | ------ | --------------------------- |
| Quotation          | DEV    | Devis                       |
| Supplier Order     | BC     | Bon de commande fournisseur |
| Client Order       | CMD    | Commande client             |
| Finished Product   | FPF    | Fiche produit fini          |
| Raw Material Label | MP     | Étiquette matière première  |
| Delivery           | LIV    | Livraison                   |
| Invoice            | FAC    | Facture                     |
| Reception          | REC    | Réception                   |
| Return             | RET    | Retour                      |
| Production         | PROD   | Production                  |
| Stock Movement     | MVT    | Mouvement de stock          |

## Changes Made

### 1. New Reference Generator (`src/utils/reference_generator.py`)

- **ReferenceGenerator class**: Core unified generation system
- **Individual functions**: Convenience functions for each document type
- **Legacy compatibility**: Maintains backward compatibility
- **Validation functions**: Check and extract reference information

### 2. Updated Dialogs

All dialog classes now use the unified system:

- `quotation_dialog.py`: Auto-generates DEV references
- `order_dialog.py`: Auto-generates CMD references
- `supplier_order_dialog.py`: Auto-generates BC references
- `raw_material_order_dialog.py`: Auto-generates BC references
- `multi_plaque_supplier_order_dialog.py`: Auto-generates BC references
- `add_finished_product_dialog.py`: Auto-generates PROD references

### 3. Updated Services

- `pdf_export_service.py`: Uses unified system for FPF and MP references
- `main_window.py`: Uses unified system for auto-generated client orders

### 4. Updated Helpers (`src/utils/helpers.py`)

- Maintains backward compatibility with existing code
- Routes to new unified system
- Provides both new and legacy format options

## Benefits

### 1. **Consistency**

- All references follow the same format
- Professional appearance across all documents
- Easy to identify document types from reference

### 2. **Uniqueness**

- Timestamp-based generation ensures uniqueness
- Sequential numbering within each second
- Collision detection and handling

### 3. **Traceability**

- Date and time embedded in reference
- Easy to sort and filter by creation time
- Clear audit trail

### 4. **Flexibility**

- Custom suffixes for specific use cases
- Supports all current and future document types
- Easy to extend for new requirements

### 5. **Backward Compatibility**

- Existing code continues to work
- Legacy functions still available
- Gradual migration possible

## Migration

### Current Status

- **New installations**: Use unified system immediately
- **Existing installations**: Continue working with mixed formats
- **User choice**: Can migrate existing references if desired

### Migration Tools

A migration script (`migrate_references.py`) is provided to:

- Analyze current reference formats
- Generate migration reports
- Preview changes before applying
- Optionally migrate existing references

### Migration Commands

```bash
# Analyze current formats
python migrate_references.py --analyze

# Generate detailed report
python migrate_references.py --report

# Preview migration changes
python migrate_references.py --preview

# Actually migrate (backup first!)
python migrate_references.py --migrate
```

## Usage Examples

### For Developers

```python
from utils.reference_generator import ReferenceGenerator

# Generate specific document types
quotation_ref = ReferenceGenerator.generate('quotation')
supplier_ref = ReferenceGenerator.generate('supplier_order')

# Generate with custom suffix
urgent_ref = ReferenceGenerator.generate('quotation', 'URGENT')

# Legacy compatibility
from utils.helpers import generate_reference
legacy_ref = generate_reference('DEV')  # Still works
```

### For Users

- All dialogs now auto-generate standardized references
- Users can still modify references if needed
- References are more professional and consistent
- Easier to identify and organize documents

## Validation and Utilities

### Format Validation

```python
# Check if reference follows new format
is_valid = ReferenceGenerator.is_standardized_format(reference)

# Extract information from reference
info = ReferenceGenerator.extract_info_from_reference(reference)
# Returns: prefix, date, time, sequence, custom_suffix
```

### Sequential Numbering

- References generated in the same second get sequential numbers
- Database-aware to prevent duplicates across document types
- Fallback mechanisms for edge cases

## Testing

The system has been thoroughly tested:

- ✅ Unique reference generation
- ✅ Format validation
- ✅ Legacy compatibility
- ✅ Application startup
- ✅ All dialogs functional
- ✅ PDF generation works

## Technical Implementation

### Database Compatibility

- Works with existing database schemas
- No database migration required
- Supports mixed old/new reference formats

### Error Handling

- Graceful fallbacks if database issues occur
- Collision detection and resolution
- Input validation for custom suffixes

### Performance

- Efficient sequential number calculation
- Minimal database queries
- Cached prefix validation

## Future Enhancements

### Possible Extensions

1. **Custom prefix configuration** per installation
2. **Reference number recycling** for deleted documents
3. **Bulk reference migration** tools
4. **Reference analytics** and reporting
5. **Integration with external systems**

### Maintenance

- The system is designed to be self-maintaining
- No regular maintenance required
- Automatic cleanup of old references possible

## Support

### If Issues Occur

1. Check application logs for reference generation errors
2. Use migration script to analyze current state
3. Verify database connectivity for sequence generation
4. Test with `utils.reference_generator` directly

### Rollback Plan

If needed, the system can be rolled back by:

1. Reverting dialog changes to use old `generate_reference()`
2. Updating `helpers.py` to use old logic
3. Existing references remain unchanged

---

**Note**: This unified system maintains full backward compatibility. Existing features continue to work exactly as before, but all new references will use the improved standardized format.
