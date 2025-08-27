# Task 004: Implement Basic ExcelIO

## Overview
**Task ID**: task-004  
**Component**: ExcelIO (Data Access Layer)  
**Dependencies**: task-002 (Constraint Data Model) ✅  
**Status**: Pending  

## Description
Implement Excel file loading functionality to read constraint data from monthly sheets into pandas DataFrames, supporting the multi-sheet format with specific column mappings.

## Architecture Context
ExcelIO is part of the Data Access Layer and provides:
- Loading Excel workbooks with multiple monthly sheets
- Parsing constraint data into DataFrames
- Sheet discovery and validation
- Memory-efficient loading for large files

## Implementation Requirements

### Core Functionality
1. **Load Excel Workbook**
   - Open Excel files using openpyxl/pandas
   - Discover available sheets (monthly tabs)
   - Validate sheet structure matches expected format
   - Handle various Excel formats (.xlsx, .xlsm)

2. **Parse Constraint Data**
   - Read specific sheet into DataFrame
   - Map columns to ConstraintRow fields
   - Handle missing/extra columns gracefully
   - Preserve data types and formatting

3. **Sheet Management**
   - List available sheets in workbook
   - Validate sheet names (e.g., "Jan", "Feb", etc.)
   - Support custom sheet name patterns
   - Cache loaded sheets for performance

### Code Locations
- Implementation: `src/data_access/excel_io.py`
- Tests: `tests/data_access/test_excel_io.py`
- Uses: `src/models/constraint_row.py::ConstraintRow`

### Interface Definition
```python
class ExcelIO:
    def __init__(self, file_path: Path):
        """Initialize with Excel file path."""
        
    def load_workbook(self) -> bool:
        """Load the Excel workbook. Returns success status."""
        
    def get_sheet_names(self) -> List[str]:
        """Return list of available sheet names."""
        
    def load_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Load specific sheet as DataFrame."""
        
    def validate_sheet_structure(self, df: pd.DataFrame) -> bool:
        """Validate DataFrame has required columns."""
        
    def get_constraint_rows(self, sheet_name: str) -> List[ConstraintRow]:
        """Load sheet and convert to ConstraintRow objects."""
```

## Test Requirements (10 focused tests)

### Core Loading Tests
1. **test_load_valid_excel_file** - Successfully open Excel workbook
2. **test_load_nonexistent_file_raises** - Handle missing files appropriately
3. **test_discover_monthly_sheets** - Find all monthly tabs
4. **test_load_sheet_to_dataframe** - Convert sheet to DataFrame

### Data Parsing Tests
5. **test_map_columns_to_constraint_fields** - Correct column mapping
6. **test_handle_missing_required_columns** - Graceful degradation
7. **test_preserve_numeric_data_types** - Maintain int/float types
8. **test_parse_constraint_rows_from_sheet** - Create ConstraintRow objects

### Error Handling Tests
9. **test_handle_corrupted_excel_file** - Recover from bad files
10. **test_handle_empty_sheets_gracefully** - Don't crash on empty data

## Acceptance Criteria
- [ ] Excel files load successfully within 5 seconds for 50MB files
- [ ] All monthly sheets are discovered and accessible
- [ ] Constraint data maps correctly to ConstraintRow model
- [ ] Missing columns are handled without crashes
- [ ] Memory usage remains reasonable for large files

## Implementation Guidelines
- Use pandas read_excel with openpyxl engine
- Implement lazy loading where possible
- Cache DataFrames to avoid re-reading
- Use chunking for very large sheets
- Follow existing patterns for error handling