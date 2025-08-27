# Task 017: Create TUI Application Shell

## Task Description
Build the main Textual application that integrates all widgets into a cohesive interface with proper layout and lifecycle management.

## Dependencies
- task-012: SheetTabs Widget (✅ completed)
- task-013: StatusBar Widget (✅ completed)
- task-015: ClusterView Base (✅ completed)

## Implementation Requirements

### Application Structure
```python
class FlowAnalysisApp(App):
    """Main TUI application for power flow constraint analysis."""
    
    # CSS for styling
    CSS = """
    #header { height: 3; }
    #main { height: 1fr; }
    #footer { height: 1; }
    """
    
    # Key bindings
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "next_sheet", "Next Sheet"),
        ("shift+tab", "prev_sheet", "Previous Sheet"),
        ("n", "next_cluster", "Next Cluster"),
        ("p", "prev_cluster", "Previous Cluster"),
    ]
```

### Widget Layout
```
+----------------------------------+
|        SheetTabs (3 lines)       |
+----------------------------------+
|                                  |
|      ClusterView (main area)     |
|                                  |
+----------------------------------+
|      StatusBar (1 line)          |
+----------------------------------+
```

### Lifecycle Management
1. **on_mount()**: Initialize data manager, load Excel file, restore session
2. **on_ready()**: Set initial sheet/cluster, update display
3. **on_resize()**: Adjust column widths in ClusterView
4. **on_exit()**: Save session state, auto-save if needed

### Data Flow
- ExcelDataManager instance shared across widgets
- SessionManager for state persistence
- Reactive properties for sheet/cluster changes
- Message passing between widgets

### Event Handling
- Sheet change events from SheetTabs
- Cell selection events from ClusterView
- Keyboard shortcuts for navigation
- Status updates to StatusBar

## Test Requirements (10 focused tests)

1. **test_app_initialization_loads_excel_file** - Startup with file loading
2. **test_widget_layout_renders_correctly** - Layout structure verification
3. **test_sheet_navigation_updates_display** - Tab/Shift+Tab functionality
4. **test_cluster_navigation_cycles_properly** - n/p key navigation
5. **test_session_restore_on_startup** - Session state restoration
6. **test_session_save_on_exit** - Clean shutdown with save
7. **test_keyboard_shortcut_handling** - All shortcuts work
8. **test_widget_communication_via_messages** - Event propagation
9. **test_error_handling_shows_user_feedback** - Graceful error display
10. **test_responsive_layout_on_resize** - Terminal resize handling

## File Locations
- **Implementation**: `src/main.py` or `src/app.py`
- **Tests**: `tests/test_application.py`

## Acceptance Criteria
- ✅ All widgets integrated and communicating
- ✅ File loaded and displayed on startup
- ✅ Navigation shortcuts working
- ✅ Session state persisted
- ✅ Clean error handling
- ✅ Responsive to terminal resize

## Performance Requirements
- Startup time < 2 seconds for typical files
- Navigation response < 100ms
- No visual lag during resize

## Code Guidelines
- Use Textual's App class properly
- Leverage reactive properties for state
- Use proper async/await for I/O operations
- Keep business logic in managers, not app
- Clear separation between UI and data layers