# Task 005: Implement Excel Save Functionality

## Task Overview
- **ID**: task-005
- **Name**: Implement Excel Save Functionality  
- **Status**: pending
- **Dependencies**: [task-004]
- **Component**: Data Access Layer
- **Module**: src/data_access/excel_io.py (extend existing)

## Task Description
Extend the ExcelIO class to save DataFrames back to Excel files with timestamped naming. This functionality is critical for persisting user edits and creating automatic backups.

## Functionality Requirements

### 1. Save Method Implementation
- **Method**: `save_data(dataframe: pd.DataFrame, sheet_name: str, original_file: str) -> str`
- Create timestamped output filename based on original
- Save DataFrame to specified sheet in Excel file
- Preserve original Excel formatting where possible
- Return the path of the saved file

### 2. Backup Creation
- Generate timestamp in format: YYYYMMDD_HHMMSS
- Output filename pattern: `{original_name}_{timestamp}.xlsx`
- Save in same directory as original file
- Create backup directory if specified in configuration

### 3. File Writing Strategy
- Use openpyxl for Excel writing
- Preserve column widths from original if available
- Apply cell formatting for numeric/percentage columns
- Handle large files efficiently (chunk writing if needed)

### 4. Error Handling
- Handle file permission errors gracefully
- Check disk space before writing
- Validate DataFrame before saving
- Provide informative error messages

## Integration Points

### Dependencies
- **ExcelIO class**: Extend existing class from task-004
- **pandas**: DataFrame operations
- **openpyxl**: Excel file writing

### Interfaces
```python
class ExcelIO:
    def save_data(
        self,
        dataframe: pd.DataFrame,
        sheet_name: str,
        original_file: str,
        backup_dir: Optional[str] = None
    ) -> str:
        """Save DataFrame to timestamped Excel file"""
        pass
    
    def _generate_filename(self, original: str, timestamp: str) -> str:
        """Generate timestamped filename"""
        pass
    
    def _apply_formatting(self, worksheet, dataframe: pd.DataFrame):
        """Apply Excel formatting to saved data"""
        pass
```

## Test Requirements (10-12 focused tests)

### Core Functionality Tests
1. **test_save_creates_file**: Verify file is created with correct name
2. **test_timestamp_format**: Check filename includes proper timestamp
3. **test_dataframe_contents_preserved**: Verify data integrity after save
4. **test_sheet_name_correct**: Ensure data saved to correct sheet

### Error Handling Tests
5. **test_permission_denied_handling**: Handle write-protected directories
6. **test_disk_full_handling**: Gracefully handle insufficient disk space
7. **test_invalid_dataframe_handling**: Handle empty/malformed DataFrames
8. **test_invalid_sheet_name**: Handle invalid Excel sheet names

### Integration Tests
9. **test_save_and_reload**: Save then reload to verify round-trip
10. **test_backup_directory_creation**: Create backup dir if not exists
11. **test_preserve_formatting**: Maintain column widths/formats
12. **test_large_file_performance**: Handle 10MB+ files efficiently

## Acceptance Criteria

### Essential Behaviors
- Creates timestamped Excel files successfully
- Preserves all data from DataFrame
- Handles common error scenarios gracefully
- Performance: Save <5MB file in <1 second

### Performance Requirements
- Save operation completes in <100ms for typical files (<1MB)
- Memory usage stays under 2x file size
- No data corruption on large files (>50MB)

## Code Guidelines

### Implementation Notes
- Use openpyxl's optimized write mode for large files
- Implement atomic writes (write to temp, then rename)
- Log all save operations for audit trail
- Keep code concise and focused

### Example Usage
```python
excel_io = ExcelIO()
dataframe = excel_io.load_data("constraints.xlsx", "Jan 2025")
# ... user makes edits to dataframe ...
saved_file = excel_io.save_data(
    dataframe, 
    "Jan 2025",
    "constraints.xlsx"
)
print(f"Saved to: {saved_file}")
# Output: "Saved to: constraints_20250827_143022.xlsx"
```

## Task Completion Checklist
- [ ] All 10-12 tests written and passing
- [ ] Save functionality implemented
- [ ] Timestamp generation working
- [ ] Error handling comprehensive
- [ ] Performance requirements met
- [ ] Code review completed
- [ ] Integration with ExcelIO verified