# Task 010: Implement Edit Operations

## Task Description
Extend ExcelDataManager with robust edit operations that include validation, error handling, and rollback capabilities. This task focuses on safely modifying data with proper validation using the DataValidator.

## Dependencies
- task-006: DataValidator (completed) - Provides validation logic for VIEW/SHORTLIMIT
- task-009: ExcelDataManager Core (pending) - Base manager to extend

## Expected Outcomes
- Safe edit operations with validation
- Proper error messages for invalid inputs
- Rollback capability for failed operations
- Edit history tracking for future undo/redo
- Integration with DataValidator for business rules

## Detailed Functionality Requirements

### Enhanced ExcelDataManager Methods
```python
# Additional methods for ExcelDataManager class

def validate_and_update(self, cluster: str, constraint_index: int,
                        column: str, value: str) -> Tuple[bool, str]:
    """
    Validate and update a value with proper error handling.
    Returns (success, message)
    """
    
def batch_update(self, updates: List[Dict]) -> Dict[str, Any]:
    """
    Apply multiple updates as a batch with transaction-like behavior.
    All succeed or all fail.
    """
    
def get_edit_history(self) -> List[EditRecord]:
    """Return list of all edits made in this session"""
    
def can_edit_column(self, column: str) -> bool:
    """Check if a column is editable based on business rules"""
    
def rollback_edit(self, edit_id: str) -> bool:
    """Rollback a specific edit by ID"""
    
def get_validation_rules(self, column: str) -> Dict[str, Any]:
    """Return validation rules for a specific column"""
```

### Edit Operation Flow
1. **Pre-validation**: Check if column is editable
2. **Value Validation**: Use DataValidator to check value
3. **Type Conversion**: Convert string input to appropriate type
4. **Update DataFrame**: Apply change to cached data
5. **History Tracking**: Record edit in history
6. **Post-validation**: Ensure data integrity maintained

### Error Handling Patterns
```python
class EditError(Exception):
    """Base exception for edit operations"""
    
class ValidationError(EditError):
    """Raised when validation fails"""
    
class ColumnNotEditableError(EditError):
    """Raised when attempting to edit read-only column"""
    
class DataIntegrityError(EditError):
    """Raised when edit would break data integrity"""
```

## How It Fits Within Architecture
- **Layer**: Business Logic Layer
- **Role**: Safe data modification with business rule enforcement
- **Consumers**: Quick Edit mode in ClusterView, keyboard shortcut handlers
- **Dependencies**: DataValidator for rules, ExcelDataManager for data access
- **Interactions**:
  - Receives edit requests from UI
  - Validates using DataValidator
  - Updates in-memory DataFrames
  - Tracks changes for persistence

## Specific Code Locations
- **Module**: `src/business_logic/excel_data_manager.py` (extend existing)
- **Imports**:
  - `from src.business_logic.data_validator import DataValidator`
  - `from src.models.edit_record import EditRecord`
  - `from typing import Tuple, List, Dict, Any`
  - `from datetime import datetime`
  - `import uuid`

## Test Requirements (10 focused tests)
1. **Valid VIEW Edit**: Update VIEW column with valid positive value
2. **Invalid VIEW Edit**: Reject negative or zero VIEW value
3. **Valid SHORTLIMIT Edit**: Update SHORTLIMIT with negative value
4. **Invalid SHORTLIMIT Edit**: Reject positive SHORTLIMIT value
5. **Empty SHORTLIMIT**: Allow empty string for SHORTLIMIT
6. **Non-editable Column**: Reject edit to read-only column (e.g., LODF)
7. **Batch Update Success**: All valid updates in batch succeed
8. **Batch Update Rollback**: One invalid update rolls back entire batch
9. **Edit History**: Track all edits with proper metadata
10. **Type Conversion**: Handle string to number conversion properly

## Acceptance Criteria
- Edits are validated before application
- Invalid edits return clear error messages
- Edit history is maintained accurately
- Batch operations are atomic (all or nothing)
- Performance: Single edit < 50ms
- Memory: Edit history limited to 1000 entries (FIFO)
- Read-only columns cannot be modified

## Code Guidelines
- Use clear validation error messages for user feedback
- Implement defensive programming for data integrity
- Use transactions/rollback pattern for batch operations
- Keep validation logic delegated to DataValidator
- Log all edit attempts for debugging
- Consider using context managers for batch operations
- Maintain immutability where possible (copy DataFrames before edits)