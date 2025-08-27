# Task 011: Implement SessionManager

## Task Overview
- **ID**: task-011
- **Name**: Implement SessionManager
- **Status**: pending
- **Dependencies**: [task-001, task-003]
- **Component**: Business Logic Layer
- **Module**: src/business_logic/session_manager.py

## Task Description
Create a SessionManager class that coordinates saving and restoring application state between sessions. This enables users to resume work exactly where they left off, maintaining context across application restarts.

## Functionality Requirements

### 1. Session Lifecycle Management
- Initialize new sessions with defaults
- Load existing session on startup
- Auto-save session state periodically
- Save session state on graceful shutdown
- Handle corrupted session recovery

### 2. State Coordination
```python
class SessionManager:
    def __init__(self, state_io: StateIO):
        """Initialize with StateIO dependency"""
        self.state_io = state_io
        self.current_state: Optional[SessionState] = None
        self.auto_save_interval = 60  # seconds
        self._last_save_time = 0
    
    def start_session(self) -> SessionState:
        """Load or create session state"""
        pass
    
    def update_state(self, **updates) -> None:
        """Update current session state"""
        pass
    
    def checkpoint(self) -> None:
        """Force save current state"""
        pass
```

### 3. State Update Tracking
- Track dirty state (changes since last save)
- Batch updates for efficiency
- Maintain state consistency
- Handle concurrent updates safely

### 4. Auto-Save Logic
- Save automatically after significant changes
- Respect auto-save interval (default 60 seconds)
- Skip saves if no changes
- Non-blocking save operations

### 5. Recovery Mechanisms
- Detect corrupted state files
- Fall back to backup states
- Create fresh session if recovery fails
- Log recovery actions for debugging

## Integration Points

### Dependencies
- **SessionState**: Data model from task-001
- **StateIO**: Persistence layer from task-003
- **datetime**: Timestamp management
- **threading**: Auto-save timer (if async)

### Interfaces
```python
class SessionManager:
    def start_session(self, state_file: str = "session.json") -> SessionState:
        """Start new or restore existing session"""
        pass
    
    def update_state(self, **updates) -> None:
        """Update session state fields"""
        pass
    
    def checkpoint(self) -> None:
        """Force immediate state save"""
        pass
    
    def should_auto_save(self) -> bool:
        """Check if auto-save needed"""
        pass
    
    def end_session(self) -> None:
        """Clean shutdown with final save"""
        pass
    
    def recover_session(self) -> SessionState:
        """Attempt to recover from corrupted state"""
        pass
```

## Test Requirements (8-10 focused tests)

### Core Functionality Tests
1. **test_new_session_creation**: Create fresh session with defaults
2. **test_existing_session_load**: Load and restore saved session
3. **test_state_updates**: Update various state fields correctly
4. **test_checkpoint_saves**: Force save works immediately

### Auto-Save Tests
5. **test_auto_save_timing**: Respects interval settings
6. **test_dirty_state_detection**: Only saves when changes exist
7. **test_auto_save_performance**: Non-blocking save operations

### Recovery Tests
8. **test_corrupted_state_recovery**: Handle invalid JSON gracefully
9. **test_missing_file_recovery**: Create new session if file missing
10. **test_session_end_cleanup**: Proper shutdown and final save

## Acceptance Criteria

### Essential Behaviors
- Sessions persist across application restarts
- Auto-save works without user intervention
- Corrupted sessions don't crash application
- State updates are atomic and consistent

### Performance Requirements
- Session load time < 100ms
- Auto-save completes < 50ms
- No UI blocking during saves
- Memory efficient state management

## Code Guidelines

### Implementation Notes
- Use composition with StateIO for persistence
- Implement dirty flag for efficient saves
- Consider using context manager for session lifecycle
- Keep session logic separate from UI concerns

### Example Usage
```python
# Application startup
state_io = StateIO("~/.ftr_tui/")
session_manager = SessionManager(state_io)
state = session_manager.start_session()

# During application use
session_manager.update_state(
    current_file="constraints.xlsx",
    current_sheet="Jan 2025",
    cursor_position=(5, 3)
)

# Periodic auto-save check
if session_manager.should_auto_save():
    session_manager.checkpoint()

# Application shutdown
session_manager.end_session()
```

### State Management Flow
```
Application Start
    ↓
Load Session (or create new)
    ↓
User Interactions → Update State
    ↓
Auto-Save Timer → Check Dirty State → Save if needed
    ↓
Application Exit → Final Save
```

## Task Completion Checklist
- [ ] All 8-10 tests written and passing
- [ ] Session lifecycle methods implemented
- [ ] Auto-save logic working
- [ ] State recovery mechanisms in place
- [ ] Integration with StateIO verified
- [ ] Performance requirements met
- [ ] Error handling comprehensive