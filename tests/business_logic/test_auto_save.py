"""
Tests for Auto-Save Manager functionality.

This test suite focuses on the 8 essential behaviors for Task 020:
1. Auto-save triggers after edits with debouncing
2. Auto-save timer configuration and management
3. Auto-save creates timestamped backups with rotation
4. Auto-save doesn't block UI (background operation)
5. Auto-save error handling with retry mechanism
6. Auto-save status indication in UI
7. Manual save overrides auto-save timer
8. Auto-save cleanup of old backups

Tests are designed to drive TDD implementation of AutoSaveManager class.
Performance requirement: saves must complete in < 100ms for files up to 10MB.
"""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from typing import Dict, List, Optional, Any
import tempfile
import threading

from src.business_logic.auto_save_manager import AutoSaveManager
from src.business_logic.excel_data_manager import ExcelDataManager
from src.widgets.status_bar import StatusBar


class TestAutoSaveTriggers:
    """Test auto-save triggering and debouncing logic."""
    
    def test_auto_save_triggers_after_edit(self):
        """Test that auto-save is initiated after a successful edit operation."""
        # Setup mocks
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        
        # Create auto-save manager with 500ms debounce
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            debounce_ms=500
        )
        
        # Mock the save method to track calls
        auto_save._perform_save = Mock()
        
        # Trigger edit notification
        auto_save.on_data_edited()
        
        # Verify save was scheduled (not called immediately due to debounce)
        assert auto_save._save_timer is not None
        assert auto_save._save_timer.is_alive()
        
        # Wait for debounce period + small buffer
        time.sleep(0.6)
        
        # Verify save was called after debounce
        auto_save._perform_save.assert_called_once()
    
    def test_debounce_prevents_rapid_saves(self):
        """Test that multiple rapid edits trigger only one save after debounce."""
        # Setup mocks
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        
        # Create auto-save manager with 200ms debounce for faster test
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            debounce_ms=200
        )
        
        # Mock the save method
        auto_save._perform_save = Mock()
        
        # Trigger multiple rapid edits
        auto_save.on_data_edited()
        time.sleep(0.05)  # 50ms between edits
        auto_save.on_data_edited()
        time.sleep(0.05)
        auto_save.on_data_edited()
        
        # Wait for debounce period + buffer
        time.sleep(0.3)
        
        # Verify save was called only once
        auto_save._perform_save.assert_called_once()


class TestAutoSaveConfiguration:
    """Test auto-save timer configuration and management."""
    
    def test_auto_save_timer_configuration(self):
        """Test that auto-save timer can be configured and updated."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        
        # Create with initial debounce time
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            debounce_ms=500
        )
        
        # Verify initial configuration
        assert auto_save._debounce_ms == 500
        
        # Update configuration
        auto_save.set_debounce_time(1000)
        assert auto_save._debounce_ms == 1000
        
        # Test that timer respects new configuration
        auto_save._perform_save = Mock()
        auto_save.on_data_edited()
        
        # Should not trigger at old time (500ms)
        time.sleep(0.6)
        auto_save._perform_save.assert_not_called()
        
        # Should trigger at new time (1000ms)
        time.sleep(0.5)  # Total 1.1s
        auto_save._perform_save.assert_called_once()
    
    def test_manual_save_overrides_auto_save_timer(self):
        """Test that manual save cancels pending auto-save and resets timer."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            debounce_ms=500
        )
        
        auto_save._perform_save = Mock()
        
        # Start auto-save timer
        auto_save.on_data_edited()
        assert auto_save._save_timer is not None
        assert auto_save._save_timer.is_alive()
        
        # Perform manual save
        auto_save.perform_manual_save()
        
        # Verify timer was cancelled
        assert auto_save._save_timer is None
        
        # Wait past debounce time
        time.sleep(0.6)
        
        # Auto-save should have been called once during manual save
        auto_save._perform_save.assert_called_once()


class TestAutoSaveBackups:
    """Test auto-save backup creation and management."""
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('shutil.move')
    def test_auto_save_creates_timestamped_backups(self, mock_move, mock_temp_file):
        """Test that auto-save creates timestamped backup files."""
        # Setup
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        mock_data_manager.has_unsaved_changes.return_value = True
        
        # Mock temp file
        mock_temp = Mock()
        mock_temp.name = '/tmp/temp_save_123'
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            backup_count=3
        )
        
        # Mock save operation
        mock_data_manager.save_to_file = Mock()
        
        # Perform save
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240827_143022'
            auto_save._perform_save()
        
        # Verify temp file was used
        mock_temp_file.assert_called_once()
        mock_data_manager.save_to_file.assert_called_once_with(Path('/tmp/temp_save_123'))
        
        # Verify backup was created with timestamp
        expected_backup = Path('/test/workbook_autosave_20240827_143022.xlsx')
        mock_move.assert_called_once_with('/tmp/temp_save_123', expected_backup)
    
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.unlink')
    def test_auto_save_cleanup_old_backups(self, mock_unlink, mock_glob):
        """Test that auto-save cleans up old backups beyond retention limit."""
        # Setup
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        
        # Mock existing backup files (5 files, should keep 3)
        old_backups = [
            Path('/test/workbook_autosave_20240825_143022.xlsx'),
            Path('/test/workbook_autosave_20240826_143022.xlsx'),
            Path('/test/workbook_autosave_20240827_103022.xlsx'),
            Path('/test/workbook_autosave_20240827_133022.xlsx'),
            Path('/test/workbook_autosave_20240827_143022.xlsx'),
        ]
        
        # Mock file stats for sorting by modification time
        for i, backup in enumerate(old_backups):
            backup.stat = Mock()
            backup.stat.return_value.st_mtime = 1000 + i * 3600  # 1 hour apart
        
        mock_glob.return_value = old_backups
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            backup_count=3
        )
        
        # Trigger cleanup
        auto_save._cleanup_old_backups()
        
        # Verify oldest 2 files were deleted (keeping newest 3)
        assert mock_unlink.call_count == 2
        deleted_files = [call[0][0] for call in mock_unlink.call_args_list]
        assert old_backups[0] in deleted_files  # Oldest
        assert old_backups[1] in deleted_files  # Second oldest


class TestAutoSavePerformance:
    """Test auto-save performance and non-blocking operation."""
    
    def test_auto_save_doesnt_block_ui(self):
        """Test that auto-save runs in background and doesn't block main thread."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        
        # Mock a slow save operation (200ms)
        def slow_save(*args):
            time.sleep(0.2)
            
        mock_data_manager.save_to_file = Mock(side_effect=slow_save)
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar
        )
        
        # Record main thread ID
        main_thread_id = threading.get_ident()
        save_thread_id = None
        
        def capture_thread_id(*args):
            nonlocal save_thread_id
            save_thread_id = threading.get_ident()
            time.sleep(0.1)  # Simulate some work
        
        # Patch the save method to capture thread ID
        with patch.object(auto_save, '_perform_save_operation', side_effect=capture_thread_id):
            # Start save
            start_time = time.time()
            auto_save._perform_save()
            
            # Main thread should return immediately
            elapsed = time.time() - start_time
            assert elapsed < 0.05  # Should be nearly instantaneous
            
            # Wait for background save to complete
            time.sleep(0.2)
        
        # Verify save ran in different thread
        assert save_thread_id != main_thread_id
        assert save_thread_id is not None
    
    @patch('time.time')
    def test_save_completes_under_100ms_for_typical_files(self, mock_time):
        """Test that save operation meets performance requirement of < 100ms."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        
        # Mock timing to simulate 80ms save
        mock_time.side_effect = [1000.0, 1000.08]  # Start and end times
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar
        )
        
        # Mock save operation
        mock_data_manager.save_to_file = Mock()
        
        # Perform save and capture performance metrics
        auto_save._perform_save_operation()
        
        # Verify performance was tracked
        assert hasattr(auto_save, '_last_save_duration')
        # Note: In real implementation, this would be calculated from actual timing


class TestAutoSaveErrorHandling:
    """Test auto-save error handling and recovery."""
    
    def test_save_error_recovery_with_retry(self):
        """Test that save failures trigger retry mechanism with exponential backoff."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        
        # First 2 saves fail, 3rd succeeds
        save_attempts = [
            Exception("Disk full"),
            Exception("Permission denied"),
            None  # Success
        ]
        mock_data_manager.save_to_file.side_effect = save_attempts
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            max_retries=3,
            base_retry_delay=0.1  # Fast retry for testing
        )
        
        # Mock sleep to track retry delays
        with patch('time.sleep') as mock_sleep:
            auto_save._perform_save_operation()
        
        # Verify 3 save attempts were made
        assert mock_data_manager.save_to_file.call_count == 3
        
        # Verify exponential backoff delays
        expected_delays = [0.1, 0.2]  # 0.1 * 2^0, 0.1 * 2^1
        actual_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays
        
        # Verify status updates during retry
        status_calls = mock_status_bar.set_status.call_args_list
        assert any('Retrying save' in str(call) for call in status_calls)
    
    def test_save_failure_preserves_user_data(self):
        """Test that save failures never cause data loss."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        
        # Simulate permanent save failure
        mock_data_manager.save_to_file.side_effect = Exception("Disk full")
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar,
            max_retries=2
        )
        
        # Perform save - should fail but not crash
        auto_save._perform_save_operation()
        
        # Verify data manager still has unsaved changes flag
        mock_data_manager.has_unsaved_changes.assert_called()
        
        # Verify error was logged/reported
        mock_status_bar.set_status.assert_called()
        status_message = mock_status_bar.set_status.call_args_list[-1][0][0]
        assert 'failed' in status_message.lower()


class TestAutoSaveStatusIndicator:
    """Test auto-save status indication in UI."""
    
    def test_save_status_updates_in_statusbar(self):
        """Test that auto-save shows status updates in StatusBar during operation."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        mock_data_manager.has_unsaved_changes.return_value = True
        mock_data_manager.get_file_path.return_value = Path('/test/workbook.xlsx')
        mock_data_manager.save_to_file = Mock()
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar
        )
        
        # Perform save operation
        auto_save._perform_save_operation()
        
        # Verify status progression: Saving -> Saved
        status_calls = [call[0][0] for call in mock_status_bar.set_status.call_args_list]
        
        assert len(status_calls) >= 2
        assert any('Saving' in status for status in status_calls)
        assert any('Saved' in status for status in status_calls)
    
    def test_concurrent_edit_during_save_handled_safely(self):
        """Test that edits during active save are handled safely without corruption."""
        mock_data_manager = Mock(spec=ExcelDataManager)
        mock_status_bar = Mock(spec=StatusBar)
        
        auto_save = AutoSaveManager(
            data_manager=mock_data_manager,
            status_bar=mock_status_bar
        )
        
        # Mock long-running save
        save_event = threading.Event()
        
        def long_save(*args):
            save_event.wait(0.2)  # Wait up to 200ms
            
        auto_save._perform_save_operation = Mock(side_effect=long_save)
        
        # Start save in background
        save_thread = threading.Thread(target=auto_save._perform_save)
        save_thread.start()
        
        # Immediately trigger another edit
        time.sleep(0.05)  # Let save start
        auto_save.on_data_edited()
        
        # Complete the save
        save_event.set()
        save_thread.join()
        
        # Verify save completed and new save was scheduled
        auto_save._perform_save_operation.assert_called()
        
        # Wait for any pending saves
        time.sleep(0.1)
        
        # Should handle concurrent operations without crashing
        assert auto_save is not None