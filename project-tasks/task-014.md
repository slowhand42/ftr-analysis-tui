# Task 014: Create ColorGrid Widget

## Task Overview
- **ID**: task-014
- **Name**: Create ColorGrid Widget
- **Status**: pending
- **Dependencies**: [task-007]
- **Component**: Presentation Layer
- **Module**: src/presentation/widgets/color_grid.py

## Task Description
Create a Textual widget that displays date/LODF values as a grid of colored blocks. This provides a compact visual representation of multiple data points with hover tooltips for detailed information.

## Functionality Requirements

### 1. Grid Layout
```
Date Grid (30 columns × N rows):
┌─────────────────────────────────────────┐
│ ████████████████████████████████████████ │ <- Constraint row 1
│ ████████████████████████████████████████ │ <- Constraint row 2
│ ████████████████████████████████████████ │ <- Constraint row 3
└─────────────────────────────────────────┘
Each █ = one day, colored by value
```

### 2. Color Mapping
- Use ColorFormatter from task-007 for consistent colors
- Support different column types (VIEW, PREV, PACTUAL, etc.)
- Apply appropriate color scheme per column type
- Handle missing/NaN values with neutral color

### 3. Interactive Features
- Hover tooltip showing:
  - Date (column header)
  - Value at position
  - Constraint name (row header)
  - Any comment if present
- Click to select cell for editing
- Keyboard navigation (arrows)
- Visual focus indicator

### 4. Widget Structure
```python
from textual.widgets import Static
from textual.reactive import reactive
from typing import Optional, List, Dict
import pandas as pd

class ColorGrid(Static):
    """Colored grid display for date-based values"""
    
    data = reactive(pd.DataFrame, always_update=True)
    column_type = reactive(str)  # VIEW, PREV, etc.
    focused_cell = reactive((0, 0))
    
    def __init__(
        self, 
        data: pd.DataFrame = None,
        column_type: str = "VIEW",
        color_formatter: ColorFormatter = None
    ):
        """Initialize with data and formatter"""
        super().__init__()
        self.data = data if data is not None else pd.DataFrame()
        self.column_type = column_type
        self.formatter = color_formatter or ColorFormatter()
    
    def render(self) -> str:
        """Render colored grid"""
        pass
    
    def get_cell_info(self, row: int, col: int) -> Dict:
        """Get tooltip info for cell"""
        pass
```

### 5. Rendering Strategy
- Use Unicode block characters for cells: █ ▓ ▒ ░
- Apply terminal colors via Rich styles
- Efficient rendering for large grids (100+ rows)
- Handle terminal width constraints
- Optional row/column labels

## Integration Points

### Dependencies
- **ColorFormatter**: From task-007 for color calculations
- **pandas**: DataFrame operations
- **Textual**: Base widget framework
- **Rich**: Terminal colors and formatting

### Events
```python
class CellSelected(Message):
    """Emitted when user selects a cell"""
    def __init__(self, row: int, col: int, value: Any):
        self.row = row
        self.col = col
        self.value = value
        super().__init__()

class CellHovered(Message):
    """Emitted when mouse hovers over cell"""
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        super().__init__()
```

## Test Requirements (10-12 focused tests)

### Display Tests
1. **test_empty_grid_render**: Handle empty DataFrame gracefully
2. **test_single_row_render**: Render grid with one row
3. **test_large_grid_render**: Efficient rendering of 100+ rows
4. **test_color_mapping**: Correct colors applied based on values

### Interaction Tests
5. **test_cell_hover_tooltip**: Tooltip shows correct information
6. **test_cell_selection**: Click selects cell correctly
7. **test_keyboard_navigation**: Arrow keys move focus
8. **test_boundary_navigation**: Handle grid edges properly

### Data Handling Tests
9. **test_nan_value_display**: Missing values shown appropriately
10. **test_data_update**: Grid updates when data changes
11. **test_column_type_switch**: Changing column type updates colors

### Performance Test
12. **test_render_performance**: Large grid renders in <100ms

## Acceptance Criteria

### Essential Behaviors
- Grid displays all data points clearly
- Colors match ColorFormatter specifications
- Interactive features work smoothly
- Performance suitable for real-time updates

### Visual Requirements
- Compact representation (1 char per cell)
- Clear color distinctions
- Readable at different terminal sizes
- Consistent with application theme

## Code Guidelines

### Implementation Notes
- Cache rendered output when possible
- Use generator for large grid rendering
- Implement virtual scrolling for huge datasets
- Keep tooltip rendering lightweight

### Example Usage
```python
from widgets.color_grid import ColorGrid, CellSelected
from business_logic.color_formatter import ColorFormatter

# Create grid with data
formatter = ColorFormatter()
df = pd.DataFrame({
    'Day1': [100, 150, 200],
    'Day2': [110, 160, 190],
    'Day3': [120, 140, 210]
})

grid = ColorGrid(
    data=df,
    column_type="VIEW",
    color_formatter=formatter
)

# Handle selection
def on_cell_selected(event: CellSelected):
    print(f"Selected: Row {event.row}, Col {event.col} = {event.value}")
```

### Visual Examples
```
# Small grid (3×3) with tooltip
┌─────────┐
│ ███░▒▓█ │  <- Row 0: high, low, medium values
│ ▓▓▓███▓ │  <- Row 1: medium, high, medium
│ ░░▒▒▓██ │  <- Row 2: low to high gradient
└─────────┘
     ↑
  Hover shows: "Day 3: 150 MW"

# Focus indicator
┌─────────┐
│ ███░[▒]█ │  <- Focused cell in brackets
└─────────┘

# With labels
     D1 D2 D3
C1 │ ███░▒▓ │
C2 │ ▓▓▓███ │
C3 │ ░░▒▒▓█ │
```

## Task Completion Checklist
- [ ] All 10-12 tests written and passing
- [ ] Grid rendering working
- [ ] Color mapping correct
- [ ] Interactive features functional
- [ ] Tooltips implemented
- [ ] Performance optimized
- [ ] Edge cases handled
- [ ] Documentation complete