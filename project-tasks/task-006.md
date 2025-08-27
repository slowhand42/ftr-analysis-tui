# Task 006: Implement DataValidator

## Overview
**Task ID**: task-006  
**Component**: DataValidator (Business Logic Layer)  
**Dependencies**: task-002 (Constraint Data Model) ✅  
**Status**: Pending  

## Description
Implement validation logic for user inputs, specifically for VIEW (must be >0) and SHORTLIMIT (must be <0 or None) columns, with comprehensive edge case handling and user-friendly error messages.

## Architecture Context
DataValidator is part of the Business Logic Layer and provides:
- Input validation before data updates
- Business rule enforcement
- User-friendly error messages
- Validation result tracking

## Implementation Requirements

### Core Functionality
1. **VIEW Column Validation**
   - Must be positive integer (>0)
   - Handle string inputs that can be converted
   - Reject zero, negative, and non-numeric values
   - Support batch validation for multiple values

2. **SHORTLIMIT Column Validation**
   - Must be negative number (<0) or None/empty
   - Allow clearing values (set to None)
   - Handle string inputs like "-100"
   - Reject positive values and zero

3. **General Validation Features**
   - Return detailed validation results
   - Provide specific error messages
   - Support custom validation rules
   - Enable/disable validation temporarily

### Code Locations
- Implementation: `src/business_logic/validators.py`
- Tests: `tests/business_logic/test_validators.py`
- Uses: `src/models/constraint_row.py::ConstraintRow`

### Interface Definition
```python
@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    sanitized_value: Optional[Any] = None

class DataValidator:
    def validate_view(self, value: Any) -> ValidationResult:
        """Validate VIEW column input (must be >0)."""
        
    def validate_shortlimit(self, value: Any) -> ValidationResult:
        """Validate SHORTLIMIT column input (<0 or None)."""
        
    def validate_cell(self, column: str, value: Any) -> ValidationResult:
        """Validate any cell based on column rules."""
        
    def sanitize_numeric_input(self, value: str) -> Optional[float]:
        """Clean and convert string input to number."""
        
    def get_column_rules(self, column: str) -> Dict[str, Any]:
        """Return validation rules for a column."""
```

## Test Requirements (12 focused tests)

### VIEW Validation Tests
1. **test_view_accepts_positive_integers** - Valid values like 1, 100, 9999
2. **test_view_rejects_zero_and_negative** - Reject 0, -1, -100
3. **test_view_handles_string_conversion** - "100" converts correctly
4. **test_view_rejects_non_numeric** - Reject "abc", special chars

### SHORTLIMIT Validation Tests
5. **test_shortlimit_accepts_negative_numbers** - Valid: -1, -100.5, -9999
6. **test_shortlimit_accepts_none_empty** - Allow clearing value
7. **test_shortlimit_rejects_positive_and_zero** - Reject 0, 1, 100
8. **test_shortlimit_handles_string_conversion** - "-100" converts

### Edge Cases Tests
9. **test_handle_whitespace_in_inputs** - Trim "  100  " correctly
10. **test_handle_decimal_inputs** - Accept 100.5 for VIEW if valid
11. **test_handle_scientific_notation** - Parse "1e3" correctly
12. **test_provide_helpful_error_messages** - Clear, actionable errors

## Acceptance Criteria
- [ ] VIEW values are strictly validated as positive
- [ ] SHORTLIMIT values are negative or None only
- [ ] String inputs are intelligently converted when possible
- [ ] Error messages clearly explain validation failures
- [ ] Validation is fast and doesn't block UI

## Implementation Guidelines
- Use try/except for type conversion attempts
- Provide specific error messages for each failure type
- Consider using regex for complex input patterns
- Cache validation rules to avoid repeated lookups
- Keep validation logic pure and stateless