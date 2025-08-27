# Task 001: Create Core Data Models

## Task Overview
**ID**: task-001  
**Type**: Data Model Implementation  
**Priority**: High  
**Dependencies**: None  
**Estimated Effort**: 2 hours  

## Description
Define the core data structures that will be used throughout the application for managing session state, tracking edits, and organizing cluster information. These models form the foundation for type safety and data consistency.

## Requirements

### SessionState Model
- Store current file path
- Track active sheet name (e.g., "SEP25")
- Remember current cluster ID
- Store current row position within cluster
- Save window dimensions

### EditRecord Model  
- Timestamp of edit
- Sheet name where edit occurred
- Row index in the DataFrame
- Column name (VIEW or SHORTLIMIT)
- Previous value (for undo functionality)
- New value applied

### ClusterInfo Model
- Unique cluster identifier
- Count of constraints in cluster
- List of CUIDs (Constraint Unique IDs) in cluster
- Optional: Cluster name/description

## Implementation Details

### Location
`/home/dev/projects/ftr/analysis-tui/src/models/data_models.py`

### Technology
- Python dataclasses for type safety
- Optional type hints for nullable fields
- JSON serialization support via dataclass_json or custom methods

### Code Structure
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple

@dataclass
class SessionState:
    last_file: str
    current_sheet: str
    current_cluster: int
    current_row: int = 0
    window_size: Tuple[int, int] = (120, 40)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        pass
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create from dictionary after JSON deserialization"""
        pass

@dataclass
class EditRecord:
    timestamp: datetime
    sheet: str
    row: int
    column: str
    old_value: Optional[float]
    new_value: float
    
    def __post_init__(self):
        """Validate column is VIEW or SHORTLIMIT"""
        pass

@dataclass  
class ClusterInfo:
    cluster_id: int
    constraint_count: int = 0
    cuid_list: List[str] = field(default_factory=list)
    
    def add_constraint(self, cuid: str):
        """Add a constraint to this cluster"""
        pass
```

## Test Requirements

### Test Coverage Goals
- 10-12 focused unit tests
- 100% coverage of model methods
- Edge case validation

### Test Scenarios
1. **SessionState Tests**
   - Create with required fields only
   - Create with all fields
   - Serialize to dictionary
   - Deserialize from dictionary
   - Handle missing optional fields in from_dict
   - Validate window_size is positive tuple

2. **EditRecord Tests**
   - Create valid edit for VIEW column
   - Create valid edit for SHORTLIMIT column
   - Reject invalid column names
   - Handle None old_value (first edit)
   - Timestamp auto-generation if not provided

3. **ClusterInfo Tests**
   - Create empty cluster
   - Add constraints and update count
   - Prevent duplicate CUIDs
   - Handle large constraint lists efficiently

## Acceptance Criteria
- [ ] All three models defined with proper type hints
- [ ] Models are immutable where appropriate (frozen=True for certain fields)
- [ ] JSON serialization/deserialization works correctly
- [ ] All validation rules enforced
- [ ] All tests pass with 100% coverage
- [ ] Models can be imported and used by other modules

## Error Handling
- Invalid column names in EditRecord raise ValueError
- Negative window dimensions raise ValueError  
- Deserialization errors provide helpful messages

## Integration Points
- SessionManager will use SessionState for persistence
- ExcelDataManager will use EditRecord for tracking changes
- ExcelDataManager will use ClusterInfo for organizing constraints

## Future Enhancements
- Add validation for sheet names against known sheets
- Add EditRecord chaining for undo/redo
- Add cluster metadata (name, description)
- Add compression for large edit histories