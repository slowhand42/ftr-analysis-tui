# Task 009: Implement ExcelDataManager Core

## Task Description
Create the central data management component that coordinates Excel data operations, cluster filtering, and sheet navigation. This manager will serve as the main interface between the presentation layer and data access layer.

## Dependencies
- task-004: Basic ExcelIO (completed) - Provides Excel loading functionality
- task-005: Excel Save Functionality (completed) - Provides Excel saving functionality

## Expected Outcomes
- Central manager class that handles all data operations
- Efficient data loading and caching for multiple sheets
- Cluster-based data filtering and retrieval
- Sheet navigation support with active sheet tracking
- Integration with ExcelIO for persistence operations

## Detailed Functionality Requirements

### Core Class: ExcelDataManager
```python
class ExcelDataManager:
    def __init__(self, excel_io: ExcelIO):
        """Initialize with ExcelIO instance for data operations"""
        
    def load_workbook(self, file_path: str) -> None:
        """Load Excel workbook and cache all sheet data"""
        
    def get_sheet_names(self) -> List[str]:
        """Return list of all sheet names in workbook"""
        
    def set_active_sheet(self, sheet_name: str) -> None:
        """Set the active sheet for operations"""
        
    def get_active_sheet_name(self) -> str:
        """Return name of currently active sheet"""
        
    def get_cluster_data(self, cluster_name: str, 
                        columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Get data for specific cluster from active sheet"""
        
    def get_all_clusters(self) -> List[str]:
        """Return list of unique cluster names in active sheet"""
        
    def update_value(self, cluster: str, constraint_index: int, 
                     column: str, value: Any) -> bool:
        """Update a cell value in the active sheet"""
        
    def save_workbook(self) -> str:
        """Save current state to timestamped Excel file"""
        
    def get_data_stats(self) -> Dict[str, Any]:
        """Return statistics about loaded data"""
```

### Key Behaviors
1. **Lazy Loading**: Load sheets on demand but cache once loaded
2. **Active Sheet Pattern**: Maintain concept of active sheet for operations
3. **Cluster Filtering**: Efficiently filter data by cluster name
4. **Data Caching**: Cache DataFrames to avoid repeated processing
5. **Change Tracking**: Track if data has been modified since load

## How It Fits Within Architecture
- **Layer**: Business Logic Layer
- **Role**: Central data orchestration
- **Consumers**: ClusterView widget, main TUI application
- **Dependencies**: ExcelIO for file operations
- **Interactions**: 
  - Receives data requests from presentation layer
  - Delegates file operations to ExcelIO
  - Manages in-memory data state and caching

## Specific Code Locations
- **Module**: `src/business_logic/excel_data_manager.py`
- **Imports**:
  - `from src.data_access.excel_io import ExcelIO`
  - `from typing import List, Optional, Dict, Any`
  - `import pandas as pd`
  - `from datetime import datetime`

## Test Requirements (12 focused tests)
1. **Initialization**: Manager initializes with ExcelIO instance
2. **Load Workbook**: Successfully loads Excel file and extracts sheets
3. **Sheet Names**: Returns correct list of sheet names
4. **Active Sheet**: Set and get active sheet correctly
5. **Invalid Sheet**: Handle setting invalid sheet name
6. **Cluster Data**: Retrieve data for specific cluster
7. **Column Filtering**: Get only specified columns for cluster
8. **All Clusters**: Return unique cluster names from active sheet
9. **Update Value**: Successfully update cell value in DataFrame
10. **Save Workbook**: Save calls ExcelIO with correct data
11. **Data Stats**: Return meaningful statistics about data
12. **Empty Cluster**: Handle request for non-existent cluster

## Acceptance Criteria
- Manager correctly loads and caches Excel data
- Sheet navigation works with proper active sheet tracking
- Cluster filtering returns correct subset of data
- Updates are reflected in cached DataFrames
- Save operation delegates correctly to ExcelIO
- Performance: Cluster data retrieval < 100ms for cached data
- Memory efficient: No duplicate DataFrame storage

## Code Guidelines
- Use descriptive variable names for DataFrames (e.g., `sheet_data` not `df`)
- Implement proper error handling for missing sheets/clusters
- Use type hints throughout for better IDE support
- Keep methods focused and under 20 lines where possible
- Document any complex filtering or transformation logic
- Consider using @property decorators for read-only attributes