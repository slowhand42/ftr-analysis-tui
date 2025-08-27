# Task 012: Create SheetTabs Widget

## Task Overview
- **ID**: task-012
- **Name**: Create SheetTabs Widget
- **Status**: pending
- **Dependencies**: None (can reference task-009 when available)
- **Component**: Presentation Layer
- **Module**: src/presentation/widgets/sheet_tabs.py

## Task Description
Create a Textual widget for displaying and navigating between monthly sheets in the Excel file. This widget provides tab-based navigation similar to Excel's sheet tabs at the bottom of the window.

## Functionality Requirements

### 1. Visual Design
```
┌─────────────────────────────────────────────────┐
│ [Jan 2025] │ Feb 2025 │ Mar 2025 │ Apr 2025 │ > │
└─────────────────────────────────────────────────┘
```
- Active tab highlighted with brackets or different style
- Inactive tabs shown with normal styling
- Scroll indicator (>) when tabs overflow
- Compact height (1-2 lines)

### 2. Tab Management
- Display all available sheet names
- Highlight currently active sheet
- Support horizontal scrolling for many sheets
- Maintain tab order from Excel file
- Handle long sheet names gracefully (truncate if needed)

### 3. Navigation Features
- Click to switch sheets
- Keyboard navigation (Tab/Shift+Tab between sheets)
- Arrow keys for tab selection
- Page Up/Down for quick navigation
- Home/End for first/last sheet

### 4. Widget Integration
```python
from textual.widgets import Static
from textual.reactive import reactive

class SheetTabs(Static):
    """Widget for sheet tab navigation"""
    
    sheet_names = reactive(list, always_update=True)
    active_index = reactive(0)
    
    def __init__(self, sheets: List[str] = None):
        """Initialize with optional sheet list"""
        super().__init__()
        if sheets:
            self.sheet_names = sheets
    
    def on_mount(self) -> None:
        """Setup widget on mount"""
        pass
    
    def render(self) -> str:
        """Render tab display"""
        pass
```

### 5. Event Handling
- Emit custom event when sheet changes
- Support programmatic sheet selection
- Handle sheet list updates dynamically
- Coordinate with main application

## Integration Points

### Dependencies
- **Textual**: Base widget framework
- **Rich**: Text formatting and styling

### Events and Messages
```python
from textual.message import Message

class SheetChanged(Message):
    """Emitted when user selects different sheet"""
    def __init__(self, sheet_name: str, sheet_index: int):
        self.sheet_name = sheet_name
        self.sheet_index = sheet_index
        super().__init__()
```

### Styling
```css
SheetTabs {
    height: 2;
    background: $surface;
    border: tall $primary;
}

SheetTabs .active-tab {
    background: $primary;
    color: $text;
    text-style: bold;
}

SheetTabs .inactive-tab {
    background: $surface;
    color: $text-muted;
}
```

## Test Requirements (8-10 focused tests)

### Display Tests
1. **test_render_single_sheet**: Display with one sheet
2. **test_render_multiple_sheets**: Display with multiple sheets
3. **test_active_sheet_highlight**: Active sheet visually distinct
4. **test_overflow_indicator**: Show scroll indicator when needed

### Navigation Tests
5. **test_click_sheet_selection**: Click changes active sheet
6. **test_keyboard_navigation**: Tab/arrows navigate sheets
7. **test_boundary_navigation**: Handle first/last sheet limits

### State Management Tests
8. **test_sheet_list_update**: Handle dynamic sheet list changes
9. **test_active_index_bounds**: Keep index within valid range
10. **test_event_emission**: Emit SheetChanged on selection

## Acceptance Criteria

### Essential Behaviors
- All sheets visible or scrollable
- Clear visual indication of active sheet
- Smooth navigation between sheets
- Events properly emitted on changes

### UI Requirements
- Fits within 1-2 lines height
- Readable tab labels
- Responsive to terminal width
- Consistent with application theme

## Code Guidelines

### Implementation Notes
- Use Textual's reactive attributes for state
- Implement efficient rendering (avoid full redraws)
- Handle edge cases (no sheets, single sheet)
- Keep widget self-contained and reusable

### Example Usage
```python
from textual.app import App
from widgets.sheet_tabs import SheetTabs, SheetChanged

class ExcelApp(App):
    def compose(self):
        sheets = ["Jan 2025", "Feb 2025", "Mar 2025"]
        yield SheetTabs(sheets)
    
    def on_sheet_changed(self, event: SheetChanged):
        self.load_sheet_data(event.sheet_name)
```

### Visual States
```
# Normal state - third sheet active
│ Jan 2025 │ Feb 2025 │ [Mar 2025] │ Apr 2025 │

# Many sheets - with scroll
│ < │ Jul 2025 │ [Aug 2025] │ Sep 2025 │ Oct 2025 │ > │

# Single sheet
│ [Jan 2025] │

# Long names - truncated
│ [January 20...] │ February 2... │ March 2025 │
```

## Task Completion Checklist
- [ ] All 8-10 tests written and passing
- [ ] Widget renders correctly
- [ ] Navigation fully functional
- [ ] Events properly emitted
- [ ] Styling matches design
- [ ] Edge cases handled
- [ ] Documentation complete