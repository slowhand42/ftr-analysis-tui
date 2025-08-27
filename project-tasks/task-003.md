# Task 003: Implement StateIO

## Overview
**Task ID**: task-003  
**Component**: StateIO (Data Access Layer)  
**Dependencies**: task-001 (Core Data Models) ✅  
**Status**: Pending  

## Description
Implement JSON persistence for session state, enabling the application to save and restore user sessions including window positions, current cluster, active sheet, and recent edits.

## Architecture Context
StateIO is part of the Data Access Layer and provides:
- Persistence of SessionState objects to JSON files
- Loading and restoration of saved sessions
- Atomic save operations to prevent data corruption
- Backward compatibility handling for older session formats

## Implementation Requirements

### Core Functionality
1. **Save Session State**
   - Convert SessionState to JSON-serializable dict
   - Write to ~/.ftr_analysis/session.json
   - Use atomic write (temp file + rename)
   - Handle permissions and disk space errors

2. **Load Session State**
   - Read from JSON file
   - Validate against SessionState model
   - Handle missing/corrupt files gracefully
   - Return default SessionState if no saved state

3. **File Management**
   - Create ~/.ftr_analysis directory if not exists
   - Handle multiple session files (backup/history)
   - Implement file locking for concurrent access
   - Clean up old session files (keep last 5)

### Code Locations
- Implementation: `src/data_access/state_io.py`
- Tests: `tests/data_access/test_state_io.py`
- Uses: `src/models/data_models.py::SessionState`

### Interface Definition
```python
class StateIO:
    def __init__(self, session_dir: Path = None):
        """Initialize with optional custom session directory."""
        
    def save_session(self, state: SessionState) -> bool:
        """Save session state to JSON file. Returns success status."""
        
    def load_session(self) -> SessionState:
        """Load session state from file or return default."""
        
    def backup_current_session(self) -> bool:
        """Create backup of current session before overwrite."""
        
    def clean_old_sessions(self, keep_count: int = 5) -> int:
        """Remove old session backups, return number deleted."""
```

## Test Requirements (8-10 focused tests)

### Core Functionality Tests
1. **test_save_session_creates_json_file** - Verify file creation and content
2. **test_load_session_returns_saved_state** - Round-trip save/load verification
3. **test_load_missing_file_returns_default** - Handle non-existent files
4. **test_atomic_save_prevents_corruption** - Verify temp file approach

### Error Handling Tests
5. **test_handle_corrupted_json_gracefully** - Malformed JSON recovery
6. **test_permission_errors_handled** - Read-only directory handling
7. **test_disk_space_error_handling** - Graceful failure on disk full

### File Management Tests
8. **test_session_directory_auto_creation** - Create ~/.ftr_analysis if needed
9. **test_backup_rotation_keeps_limit** - Only keep last N backups
10. **test_concurrent_access_safety** - File locking for multi-instance

## Acceptance Criteria
- [ ] Session state persists between application runs
- [ ] Corrupt files don't crash the application
- [ ] Atomic saves prevent partial writes
- [ ] Old sessions are automatically cleaned up
- [ ] All file operations handle errors gracefully

## Implementation Guidelines
- Use pathlib for all path operations
- Implement context managers for file operations
- Use json module with custom encoder for datetime
- Follow existing error handling patterns
- Keep implementation concise and focused