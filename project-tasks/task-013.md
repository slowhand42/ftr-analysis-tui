# Task 013: Create StatusBar Widget

## Task Overview
**ID**: task-013  
**Type**: Widget Implementation  
**Priority**: Medium  
**Dependencies**: None  
**Estimated Effort**: 2 hours  

## Description
Create a status bar widget that displays current position information, help text, and system status. This widget provides essential context to users about their current location in the data and available commands.

## Requirements

### Display Elements
1. **Current Position**
   - Sheet name (e.g., "SEP25")
   - Cluster ID and total clusters (e.g., "Cluster 42 of 156")
   - Row position within cluster (e.g., "Row 3 of 7")
   - Current column if editing (e.g., "Editing: VIEW")

2. **File Information**
   - Current file name (truncated if needed)
   - Save status indicator (saved/modified)
   - Last save timestamp

3. **Help Text**
   - Context-sensitive keyboard shortcuts
   - Current mode (browse/edit)
   - Quick command reminders

4. **System Status**
   - Memory usage (if high)
   - Performance indicators
   - Error/warning messages (temporary)

## Implementation Details

### Location
`/home/dev/projects/ftr/analysis-tui/src/widgets/status_bar.py`

### Technology
- Textual Static widget for efficient updates
- Rich Text for formatting
- Reactive properties for automatic updates

### Code Structure
```python
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from datetime import datetime
from typing import Optional

class StatusBar(Static):
    """Status bar showing position, file info, and help text"""
    
    # Reactive properties that trigger re-render
    current_sheet: reactive[str] = reactive("SEP25")
    current_cluster: reactive[int] = reactive(0)
    total_clusters: reactive[int] = reactive(0)
    current_row: reactive[int] = reactive(0)
    total_rows: reactive[int] = reactive(0)
    file_name: reactive[str] = reactive("")
    is_modified: reactive[bool] = reactive(False)
    last_save: reactive[Optional[datetime]] = reactive(None)
    edit_mode: reactive[bool] = reactive(False)
    edit_column: reactive[str] = reactive("")
    message: reactive[str] = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_display()
    
    def update_position(self, sheet: str, cluster: int, 
                        row: int, total_rows: int):
        """Update position information"""
        self.current_sheet = sheet
        self.current_cluster = cluster
        self.current_row = row
        self.total_rows = total_rows
    
    def set_file_info(self, file_name: str, modified: bool = False):
        """Update file information"""
        self.file_name = self._truncate_filename(file_name)
        self.is_modified = modified
    
    def set_edit_mode(self, editing: bool, column: str = ""):
        """Update edit mode status"""
        self.edit_mode = editing
        self.edit_column = column
    
    def show_message(self, message: str, duration: float = 3.0):
        """Display temporary message"""
        self.message = message
        # Set timer to clear message after duration
    
    def render(self) -> Text:
        """Render the status bar"""
        # Build status text with three sections
        left = self._build_position_text()
        center = self._build_file_text()
        right = self._build_help_text()
        
        return self._combine_sections(left, center, right)
    
    def _build_position_text(self) -> Text:
        """Build position section"""
        text = Text()
        text.append(f"{self.current_sheet} | ")
        text.append(f"Cluster {self.current_cluster}/{self.total_clusters} | ")
        text.append(f"Row {self.current_row}/{self.total_rows}")
        if self.edit_mode:
            text.append(f" | Editing: {self.edit_column}", style="bold yellow")
        return text
    
    def _build_file_text(self) -> Text:
        """Build file info section"""
        text = Text()
        text.append(self.file_name)
        if self.is_modified:
            text.append(" *", style="bold red")
        if self.last_save:
            save_time = self.last_save.strftime("%H:%M:%S")
            text.append(f" | Saved: {save_time}")
        return text
    
    def _build_help_text(self) -> Text:
        """Build context-sensitive help text"""
        if self.edit_mode:
            return Text("[Enter] Save | [Esc] Cancel | [Tab] Next Field")
        else:
            return Text("[n/p] Navigate | [0-9] Edit | [Ctrl+S] Save | [?] Help")
    
    def _truncate_filename(self, filename: str, max_len: int = 30) -> str:
        """Truncate long filenames"""
        if len(filename) <= max_len:
            return filename
        return "..." + filename[-(max_len-3):]
    
    def _combine_sections(self, left: Text, center: Text, 
                          right: Text) -> Text:
        """Combine sections with proper spacing"""
        # Calculate spacing based on terminal width
        # Align left, center, right with appropriate padding
        pass
```

## Test Requirements

### Test Coverage Goals
- 8 focused unit tests
- Test reactive property updates
- Test text formatting

### Test Scenarios
1. **Position Updates**
   - Update sheet, cluster, row
   - Handle edge cases (0 values, large numbers)

2. **File Information**
   - Display filename with truncation
   - Show modified indicator
   - Update save timestamp

3. **Edit Mode**
   - Switch between browse and edit modes
   - Display correct column being edited
   - Update help text appropriately

4. **Message Display**
   - Show temporary messages
   - Clear messages after timeout
   - Handle multiple messages

5. **Text Formatting**
   - Proper section alignment
   - Color styles applied correctly
   - Handle narrow terminal widths

## Acceptance Criteria
- [ ] Displays all required information sections
- [ ] Updates reactively when properties change
- [ ] Truncates long filenames appropriately
- [ ] Shows context-sensitive help text
- [ ] Handles terminal resize gracefully
- [ ] All tests pass with good coverage

## Widget Styling

### CSS Classes
```css
StatusBar {
    height: 1;
    background: $primary-background;
    color: $text;
    dock: bottom;
}

StatusBar .position {
    color: $text-muted;
}

StatusBar .modified {
    color: $error;
    text-style: bold;
}

StatusBar .editing {
    color: $warning;
    text-style: bold;
}

StatusBar .help {
    color: $text-muted;
    text-style: italic;
}
```

## Integration Points
- Main app updates position on navigation
- ExcelDataManager triggers file info updates
- ClusterView notifies of edit mode changes
- Auto-save updates save timestamp

## Message Priority System
1. Error messages (highest priority, red)
2. Warning messages (medium priority, yellow)
3. Info messages (low priority, default color)
4. Status updates (lowest priority, muted)

## Performance Considerations
- Throttle updates to max 10/second
- Cache formatted text when possible
- Use reactive properties efficiently
- Avoid expensive computations in render()

## Future Enhancements
- Add progress bar for long operations
- Show undo/redo stack depth
- Display keyboard macro recording status
- Add network status for future collaboration
- Show performance metrics (response time)