# Task 002: Create Constraint Data Model

## Task Overview
**ID**: task-002  
**Type**: Data Model Implementation  
**Priority**: High  
**Dependencies**: None  
**Estimated Effort**: 2 hours  

## Description
Define the data structure representing a single constraint row with all columns specified in the PRD. This model will be used for type-safe access to constraint data and will integrate with pandas DataFrames.

## Requirements

### Core Columns (Must Have)
- CLUSTER: Cluster identifier (int)
- CUID: Constraint Unique ID - PRIMARY KEY (str)
- VIEW: Primary editable value (float, must be >0)
- PREV: Previous auction's VIEW value (float)
- PACTUAL: Predictor with forecasted variables (float)
- PEXPECTED: Predictor with typical variables (float)
- VIEWLG: Logarithmic view value (float)
- SHORTLIMIT: Secondary editable value (Optional[float], must be <0 or None)

### Monitor & Contingency Columns
- MON: Monitor/element name (str)
- CONT: Contingency description (str)
- DIRECTION: Flow direction (int, -1 or 1)
- SOURCE: Source node - monthly sheets only (Optional[str])
- SINK: Sink node - monthly sheets only (Optional[str])

### Flow & Limit Columns
- FLOW: Current flow value (float)
- LIMIT: MW limit (float)
- LAST_BINDING: Last binding date (Optional[str])
- BHOURS: Binding hours (float)
- MAXHIST: Maximum historical value (float)

### Exposure & Delta Columns
- EXP_PEAK: Existing exposure peak (float)
- EXP_OP: Existing exposure operating (float)
- RECENT_DELTA: Recent forecast vs realized (float)

### Grid Data (Complex Types)
- date_grid_values: List of daily values (List[float])
- date_grid_comments: Transmission outage info (Dict[int, str])
- lodf_grid_values: List of LODF values (List[float])

## Implementation Details

### Location
`/home/dev/projects/ftr/analysis-tui/src/models/data_models.py`

### Technology
- Python dataclass with Optional types for nullable fields
- Integration with pandas for DataFrame compatibility
- Property methods for computed values

### Code Structure
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class ConstraintRow:
    """Represents a single constraint row from the Excel sheet"""
    
    # Primary identifiers
    cluster: int
    cuid: str  # Primary key
    
    # Editable values
    view: float
    shortlimit: Optional[float] = None
    
    # Predictor values
    prev: float = 0.0
    pactual: float = 0.0
    pexpected: float = 0.0
    viewlg: float = 0.0
    
    # Monitor and contingency
    mon: str = ""
    cont: str = ""
    direction: int = 1  # -1 or 1
    source: Optional[str] = None  # Monthly sheets only
    sink: Optional[str] = None    # Monthly sheets only
    
    # Flow and limits
    flow: float = 0.0
    limit: float = 0.0
    last_binding: Optional[str] = None
    bhours: float = 0.0
    maxhist: float = 0.0
    
    # Exposure and delta
    exp_peak: float = 0.0
    exp_op: float = 0.0
    recent_delta: float = 0.0
    
    # Grid data (complex types)
    date_grid_values: List[float] = field(default_factory=list)
    date_grid_comments: Dict[int, str] = field(default_factory=dict)
    lodf_grid_values: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate constraints after initialization"""
        self.validate()
    
    def validate(self):
        """Validate business rules"""
        if self.view <= 0:
            raise ValueError(f"VIEW must be positive, got {self.view}")
        if self.shortlimit is not None and self.shortlimit >= 0:
            raise ValueError(f"SHORTLIMIT must be negative, got {self.shortlimit}")
        if self.direction not in (-1, 1):
            raise ValueError(f"DIRECTION must be -1 or 1, got {self.direction}")
    
    @classmethod
    def from_dataframe_row(cls, row: dict) -> 'ConstraintRow':
        """Create from pandas DataFrame row"""
        pass
    
    def to_dataframe_dict(self) -> dict:
        """Convert to dictionary for DataFrame update"""
        pass
    
    @property
    def is_binding(self) -> bool:
        """Check if constraint is currently binding"""
        return self.flow >= self.limit * 0.95
    
    @property
    def has_outages(self) -> bool:
        """Check if date grid has transmission outages"""
        return len(self.date_grid_comments) > 0
```

## Test Requirements

### Test Coverage Goals
- 8-10 focused unit tests
- Cover all validation rules
- Test DataFrame integration

### Test Scenarios
1. **Valid Creation Tests**
   - Create with minimal required fields
   - Create with all fields populated
   - Create from DataFrame row dict

2. **Validation Tests**  
   - Reject VIEW <= 0
   - Reject SHORTLIMIT >= 0 (when not None)
   - Reject DIRECTION not in (-1, 1)
   - Accept SHORTLIMIT = None

3. **DataFrame Integration Tests**
   - Convert from DataFrame row
   - Convert to DataFrame dict
   - Handle missing optional columns

4. **Property Tests**
   - Test is_binding calculation
   - Test has_outages detection

## Acceptance Criteria
- [ ] Model includes all columns from PRD
- [ ] Validation rules enforced for VIEW, SHORTLIMIT, DIRECTION
- [ ] DataFrame conversion methods work bidirectionally
- [ ] Optional fields handle None gracefully
- [ ] Complex grid data structures properly initialized
- [ ] All tests pass with good coverage

## Error Handling
- Clear error messages for validation failures
- Graceful handling of missing DataFrame columns
- Type conversion errors caught and reported

## Integration Points
- ExcelDataManager will convert DataFrame rows to ConstraintRow
- DataValidator will use model's validation rules
- ColorFormatter will access model properties for formatting
- ClusterView will display model data

## Column Mapping
Map Excel column names to model attributes:
```python
COLUMN_MAPPING = {
    'CLUSTER': 'cluster',
    'CUID': 'cuid', 
    'VIEW': 'view',
    'SHORTLIMIT': 'shortlimit',
    'PREV': 'prev',
    'PACTUAL': 'pactual',
    'PEXPECTED': 'pexpected',
    'VIEWLG': 'viewlg',
    'MON': 'mon',
    'CONT': 'cont',
    'DIRECTION': 'direction',
    'SOURCE': 'source',
    'SINK': 'sink',
    'FLOW': 'flow',
    'LIMIT': 'limit',
    'LAST_BINDING': 'last_binding',
    'BHOURS': 'bhours',
    'MAXHIST': 'maxhist',
    'EXP_PEAK': 'exp_peak',
    'EXP_OP': 'exp_op',
    'RECENT_DELTA': 'recent_delta'
}
```

## Future Enhancements
- Add calculated properties (e.g., congestion risk score)
- Add methods for merging with historical data
- Add serialization for caching
- Support for additional grid types