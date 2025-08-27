# Task 015: Create ClusterView Base

## Task Description
Create the main DataTable widget for displaying cluster constraint data with proper formatting, scrolling, and cell selection. This is the core visual component that users will interact with for viewing and editing constraints.

## Dependencies
- task-009: ExcelDataManager (pending) - Provides data for display
- task-007: ColorFormatter (completed) - Provides color formatting for cells

## Expected Outcomes
- Textual DataTable subclass optimized for constraint display
- Proper column formatting with colors from ColorFormatter
- Smooth scrolling and navigation
- Cell selection and highlighting
- Integration with data manager for live updates
- Responsive to window resizing

## Detailed Functionality Requirements

### Core Class: ClusterView
```python
from textual.widgets import DataTable
from textual.binding import Binding
from textual.reactive import reactive

class ClusterView(DataTable):
    """DataTable specialized for cluster constraint display"""
    
    # Reactive properties
    current_cluster = reactive("")
    selected_cell = reactive((0, 0))
    
    def __init__(self, data_manager: ExcelDataManager, 
                 color_formatter: ColorFormatter):
        """Initialize with data source and formatter"""
        
    def load_cluster(self, cluster_name: str) -> None:
        """Load and display data for specified cluster"""
        
    def refresh_display(self) -> None:
        """Refresh current display with latest data"""
        
    def get_selected_value(self) -> str:
        """Return value of currently selected cell"""
        
    def highlight_editable_columns(self) -> None:
        """Visually indicate which columns can be edited"""
        
    def apply_cell_formatting(self, row: int, col: int) -> None:
        """Apply color formatting to specific cell"""
        
    def on_mount(self) -> None:
        """Setup table when widget mounts"""
        
    def action_move_cursor(self, direction: str) -> None:
        """Handle arrow key navigation"""
```

### Column Configuration
```python
COLUMN_CONFIG = {
    'CONSTRAINTNAME': {'width': 30, 'editable': False},
    'BRANCHNAME': {'width': 25, 'editable': False},
    'VIEW': {'width': 10, 'editable': True, 'format': 'number'},
    'PREV': {'width': 10, 'editable': False, 'format': 'number'},
    'PACTUAL': {'width': 12, 'editable': False, 'format': 'number'},
    'PEXPECTED': {'width': 12, 'editable': False, 'format': 'number'},
    'RECENT_DELTA': {'width': 14, 'editable': False, 'format': 'delta'},
    'SHORTLIMIT': {'width': 12, 'editable': True, 'format': 'number'},
    'LODF': {'width': 10, 'editable': False, 'format': 'percent'},
    'STATUS': {'width': 15, 'editable': False}
}
```

### Display Features
1. **Smart Column Widths**: Auto-adjust based on content and window size
2. **Row Striping**: Alternating row colors for readability
3. **Cell Borders**: Clear visual separation between cells
4. **Header Styling**: Bold, distinct headers
5. **Focus Indicators**: Clear highlight for selected cell
6. **Scroll Indicators**: Show position in large datasets

### Formatting Rules
1. **Numbers**: Right-aligned, thousand separators
2. **Percentages**: Show with % symbol, 2 decimal places
3. **Empty Cells**: Show as "-" or grayed out
4. **Colors**: Apply ColorFormatter rules per column
5. **Editable Cells**: Subtle border or background difference

## How It Fits Within Architecture
- **Layer**: Presentation Layer
- **Role**: Primary data display widget
- **Consumers**: Main TUI application
- **Dependencies**: ExcelDataManager for data, ColorFormatter for styling
- **Interactions**:
  - Receives cluster data from manager
  - Applies formatting from ColorFormatter
  - Emits events for cell selection/edit requests
  - Updates display on data changes

## Specific Code Locations
- **Module**: `src/presentation/widgets/cluster_view.py`
- **Imports**:
  - `from textual.widgets import DataTable`
  - `from textual.binding import Binding`
  - `from textual.reactive import reactive`
  - `from src.business_logic.excel_data_manager import ExcelDataManager`
  - `from src.business_logic.color_formatter import ColorFormatter`
  - `import pandas as pd`

## Test Requirements (12 focused tests)
1. **Initialize Widget**: Create with manager and formatter
2. **Load Cluster Data**: Display correct data for cluster
3. **Column Headers**: Show all required columns with proper names
4. **Cell Formatting**: Apply colors from ColorFormatter correctly
5. **Cell Selection**: Track and highlight selected cell
6. **Arrow Navigation**: Move selection with arrow keys
7. **Empty Data**: Handle empty cluster gracefully
8. **Refresh Display**: Update when underlying data changes
9. **Editable Indicators**: Show which columns can be edited
10. **Window Resize**: Adjust column widths appropriately
11. **Large Dataset**: Handle 1000+ rows efficiently
12. **Get Selected Value**: Return correct value for selected cell

## Acceptance Criteria
- Widget displays all constraint data clearly
- Colors are applied correctly per ColorFormatter rules
- Navigation is smooth and responsive
- Selected cell is clearly highlighted
- Editable columns are visually distinct
- Performance: Initial load < 200ms for 500 rows
- Memory: Efficient handling of large datasets (5000+ rows)
- Scrolling is smooth without flicker

## Code Guidelines
- Use Textual's reactive properties for state management
- Implement efficient rendering for large datasets
- Cache formatted values to avoid repeated calculations
- Use proper event handlers for user interactions
- Keep formatting logic separate from data logic
- Document any Textual-specific patterns used
- Consider virtual scrolling for very large datasets