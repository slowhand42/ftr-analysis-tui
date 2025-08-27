# Task 020: Implement Auto-Save

## Task Description
Add automatic save functionality that triggers after edits, with performance optimization to ensure saves complete in under 100ms.

## Dependencies
- task-010: Edit Operations (✅ completed)
- task-005: Excel Save Functionality (✅ completed)

## Implementation Requirements

### Auto-Save Trigger System
- Trigger save after any successful edit operation
- Debounce multiple rapid edits (wait 500ms after last edit)
- Run save in background thread to avoid blocking UI
- Track save status and show in StatusBar

### Save Strategy
1. **Incremental Save**: Only write changed sheets
2. **Background Processing**: Use threading/async for save
3. **Atomic Operations**: Write to temp file, then rename
4. **Backup Retention**: Keep last 3 auto-save versions

### Performance Optimization
- Cache unchanged data to avoid rewriting
- Use optimized Excel writer settings
- Batch multiple edits before save
- Profile and optimize hot paths

### Error Recovery
- Retry failed saves with exponential backoff
- Fall back to alternative save location if needed
- Log all save errors for debugging
- Never lose user edits due to save failure

### Status Feedback
- Show save indicator in StatusBar
- Display "Saving..." during operation
- Show "Saved" confirmation briefly
- Alert user if save fails

## Test Requirements (10 focused tests)

1. **test_auto_save_triggers_after_edit** - Save initiated after value change
2. **test_debounce_prevents_rapid_saves** - Multiple edits trigger single save
3. **test_save_completes_under_100ms** - Performance requirement met
4. **test_background_save_doesnt_block_ui** - UI remains responsive
5. **test_incremental_save_only_changed_sheets** - Optimization working
6. **test_atomic_save_prevents_corruption** - Temp file strategy
7. **test_backup_versions_maintained** - Rotation of backups
8. **test_save_error_recovery_with_retry** - Resilient to failures
9. **test_save_status_updates_in_statusbar** - User feedback
10. **test_concurrent_edit_during_save** - Thread safety

## File Locations
- **Implementation**: `src/business_logic/auto_save_manager.py`
- **Tests**: `tests/test_auto_save.py`

## Acceptance Criteria
- ✅ Automatic save after edits
- ✅ Performance < 100ms for typical files
- ✅ No data loss on failures
- ✅ Clear user feedback
- ✅ Background operation
- ✅ Backup versioning

## Performance Requirements
- Save completion < 100ms for files up to 10MB
- Save completion < 500ms for files up to 50MB
- No UI blocking during save
- Memory usage increase < 10MB during save

## Code Guidelines
- Use threading or asyncio for background saves
- Implement proper debouncing logic
- Use context managers for file operations
- Add comprehensive error handling
- Profile performance with realistic data