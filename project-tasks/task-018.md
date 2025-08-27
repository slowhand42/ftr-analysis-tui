# Task 018: Implement Navigation Logic

## Overview
Implement comprehensive navigation logic for the TUI application, enabling users to navigate between clusters (n/p keys), switch sheets (Tab), and move through the grid efficiently.

## Dependencies
- task-017: TUI Application Shell ✅

## Detailed Requirements

### 1. Cluster Navigation
- **n key**: Navigate to next cluster
- **p key**: Navigate to previous cluster
- **Wrap around**: At last cluster, 'n' goes to first; at first, 'p' goes to last
- **State preservation**: Maintain cursor position within cluster when switching

### 2. Sheet Navigation
- **Tab key**: Switch between monthly sheets
- **Shift+Tab**: Previous sheet (optional enhancement)
- **Persistence**: Remember active cluster per sheet
- **Visual feedback**: Update sheet tabs widget highlighting

### 3. Grid Navigation (within cluster)
- **Arrow keys**: Move cell selection up/down/left/right
- **Home/End**: Jump to first/last column in row
- **PageUp/PageDown**: Move one screen up/down
- **Ctrl+Home/End**: Jump to top/bottom of grid

### 4. Navigation State Management
- Track current position: sheet, cluster, row, column
- Maintain navigation history for potential undo
- Coordinate with SessionManager for persistence
- Ensure navigation respects data boundaries

### 5. Integration Points
- **AnalysisTUIApp**: Register keyboard handlers
- **ClusterView**: Update display on navigation
- **SheetTabs**: Sync visual state
- **StatusBar**: Update position display

## Test Requirements (12 focused tests)

1. **test_cluster_navigation_forward** - 'n' key moves to next cluster
2. **test_cluster_navigation_backward** - 'p' key moves to previous cluster
3. **test_cluster_navigation_wrapping** - Proper wrap-around at boundaries
4. **test_sheet_switching_via_tab** - Tab key changes sheets
5. **test_grid_arrow_navigation** - Arrow keys move selection
6. **test_home_end_navigation** - Home/End keys work correctly
7. **test_page_navigation** - PageUp/Down moves by screen
8. **test_navigation_bounds_checking** - Cannot navigate outside data
9. **test_navigation_state_persistence** - State saved between navigations
10. **test_navigation_with_empty_data** - Handles missing clusters gracefully
11. **test_navigation_performance** - Fast response (<100ms)
12. **test_navigation_event_coordination** - Events update all widgets

## Implementation Guidelines

### Code Structure
```python
# In src/presentation/navigation_controller.py
class NavigationController:
    def __init__(self, app: AnalysisTUIApp):
        self.app = app
        self.current_sheet = 0
        self.current_cluster = 0
        self.current_row = 0
        self.current_col = 0
    
    def navigate_cluster(self, direction: int):
        """Navigate to next/previous cluster"""
    
    def switch_sheet(self, sheet_index: int):
        """Switch to different sheet"""
    
    def move_cursor(self, dx: int, dy: int):
        """Move cursor within grid"""
```

### Key Bindings Registration
```python
# In AnalysisTUIApp
def compose(self):
    yield self.navigation_controller
    
def on_key(self, event: Key):
    if event.key == "n":
        self.navigation_controller.navigate_cluster(1)
    elif event.key == "p":
        self.navigation_controller.navigate_cluster(-1)
```

## Acceptance Criteria
- [ ] All navigation keys work as specified in PRD
- [ ] Navigation is smooth and responsive (<100ms)
- [ ] Visual feedback updates immediately
- [ ] State persists correctly
- [ ] Boundaries are respected
- [ ] All 12 tests pass

## Performance Requirements
- Navigation response time: <100ms
- No visible lag when switching clusters/sheets
- Efficient memory usage (no data duplication)

## Error Handling
- Handle empty sheets gracefully
- Prevent out-of-bounds navigation
- Clear error messages for navigation failures
- Fallback to safe defaults on errors