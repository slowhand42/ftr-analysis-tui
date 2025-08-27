# Task 019: Implement Keyboard Shortcuts

## Overview
Implement all keyboard shortcuts defined in the PRD for efficient user interaction, including save, quit, help, and edit operations.

## Dependencies
- task-017: TUI Application Shell ✅
- task-016: Quick Edit Mode ✅

## Detailed Requirements

### 1. File Operations
- **Ctrl+S**: Save current changes to Excel file
  - Trigger auto-save immediately
  - Show confirmation message
  - Update status bar modified indicator
- **Ctrl+Q**: Quit application
  - Check for unsaved changes
  - Prompt for confirmation if modified
  - Clean shutdown with session save

### 2. Edit Operations
- **Number keys (0-9)**: Trigger quick edit mode (already implemented in task-016)
- **Enter**: Commit current edit
- **Escape**: Cancel current edit
- **Ctrl+Z**: Undo last edit (if history available)
- **Ctrl+Y**: Redo (if history available)

### 3. View Operations
- **F1 or ?**: Show help screen with all shortcuts
- **F5**: Refresh data from file
- **Ctrl+L**: Redraw screen (clear artifacts)

### 4. Navigation Shortcuts (coordinated with task-018)
- **n/p**: Next/Previous cluster
- **Tab**: Next sheet
- **Arrow keys**: Cell navigation
- **Home/End**: Row navigation
- **PageUp/Down**: Page navigation

### 5. Shortcut Conflict Resolution
- Number keys only trigger edit in appropriate context
- Escape has priority to cancel operations
- Ctrl combinations override single keys
- Help screen shows context-sensitive shortcuts

## Test Requirements (10 focused tests)

1. **test_save_shortcut_triggers_save** - Ctrl+S saves file correctly
2. **test_quit_with_confirmation** - Ctrl+Q prompts if unsaved changes
3. **test_help_screen_display** - F1 shows comprehensive help
4. **test_refresh_data_shortcut** - F5 reloads from file
5. **test_edit_shortcuts_integration** - Enter/Escape work in edit mode
6. **test_shortcut_priority_handling** - Conflicts resolved correctly
7. **test_disabled_shortcuts_in_edit_mode** - Navigation disabled during edit
8. **test_shortcut_feedback_messages** - User gets confirmation
9. **test_shortcut_performance** - All respond in <50ms
10. **test_help_screen_navigation** - Can scroll/close help screen

## Implementation Guidelines

### Code Structure
```python
# In src/presentation/shortcut_manager.py
class ShortcutManager:
    def __init__(self, app: AnalysisTUIApp):
        self.app = app
        self.shortcuts = self._register_shortcuts()
    
    def _register_shortcuts(self):
        return {
            "ctrl+s": self.save_file,
            "ctrl+q": self.quit_app,
            "f1": self.show_help,
            "?": self.show_help,
            "f5": self.refresh_data,
            "ctrl+l": self.redraw_screen,
        }
    
    async def handle_key(self, key: str, context: str):
        """Route key to appropriate handler based on context"""
```

### Help Screen Content
```python
HELP_TEXT = """
Flow Analysis TUI - Keyboard Shortcuts

FILE OPERATIONS:
  Ctrl+S    Save changes
  Ctrl+Q    Quit application
  F5        Refresh data

NAVIGATION:
  n/p       Next/Previous cluster  
  Tab       Next sheet
  ↑↓←→      Move cursor
  Home/End  Start/End of row
  PgUp/PgDn Page up/down

EDITING:
  0-9       Start quick edit
  Enter     Commit edit
  Escape    Cancel edit

Press Escape to close help
"""
```

### Integration with App
```python
# In AnalysisTUIApp
async def on_key(self, event: Key):
    if self.in_edit_mode:
        await self.edit_handler.process_key(event)
    else:
        await self.shortcut_manager.handle_key(event.key, self.context)
```

## Acceptance Criteria
- [ ] All PRD shortcuts implemented
- [ ] Help screen shows all shortcuts
- [ ] Shortcuts respond quickly (<50ms)
- [ ] Proper context handling (edit vs normal mode)
- [ ] Save confirmation messages work
- [ ] Quit prompts for unsaved changes
- [ ] All 10 tests pass

## Performance Requirements
- Shortcut response time: <50ms
- Help screen renders instantly
- Save operation completes in <100ms for typical files

## Error Handling
- Invalid shortcuts ignored silently
- Save failures show clear error message
- Quit always possible (force quit option)
- Help screen always accessible