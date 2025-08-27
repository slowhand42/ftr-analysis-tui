"""Test suite for SessionManager state coordination and auto-save functionality.

This test suite drives the TDD implementation of SessionManager, covering:
- Session lifecycle management
- Auto-save timer functionality  
- State synchronization and updates
- Recovery mechanisms
- Performance requirements
"""

import pytest
import time
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from threading import Event

from src.business_logic.session_manager import SessionManager
from src.io.state_io import StateIO
from src.models.data_models import SessionState, EditRecord


class TestSessionManagerInitialization:
    """Test session creation and loading functionality."""
    
    def test_new_session_creation(self):
        """Test creating a fresh session with default values."""
        # Arrange
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = SessionState(
            last_file="", 
            current_sheet="", 
            current_cluster=0
        )
        
        # Act
        session_manager = SessionManager(mock_state_io)
        session_state = session_manager.start_session()
        
        # Assert
        assert session_state is not None
        assert session_state.last_file == ""
        assert session_state.current_sheet == ""
        assert session_state.current_cluster == 0
        assert session_state.current_row == 0
        assert isinstance(session_state.last_modified, datetime)
        mock_state_io.load_session.assert_called_once()
    
    def test_existing_session_load(self):
        """Test loading and restoring a previously saved session."""
        # Arrange
        expected_session = SessionState(
            last_file="test_file.xlsx",
            current_sheet="Jan 2025", 
            current_cluster=5,
            current_row=10,
            window_size=(100, 30),
            last_modified=datetime(2025, 1, 1, 12, 0, 0)
        )
        
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = expected_session
        
        # Act
        session_manager = SessionManager(mock_state_io)
        loaded_session = session_manager.start_session()
        
        # Assert
        assert loaded_session == expected_session
        assert loaded_session.last_file == "test_file.xlsx"
        assert loaded_session.current_sheet == "Jan 2025"
        assert loaded_session.current_cluster == 5
        assert loaded_session.current_row == 10
        assert loaded_session.window_size == (100, 30)
        mock_state_io.load_session.assert_called_once()


class TestSessionStateUpdates:
    """Test state update and synchronization functionality."""
    
    def test_state_updates_with_dirty_tracking(self):
        """Test updating various state fields correctly with dirty flag tracking."""
        # Arrange
        initial_session = SessionState(
            last_file="old_file.xlsx",
            current_sheet="Dec 2024",
            current_cluster=1
        )
        
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        
        # Act
        session_manager.update_state(
            current_file="new_file.xlsx",
            current_sheet="Jan 2025", 
            cursor_position=(8, 5)
        )
        
        # Assert
        current_state = session_manager.current_state
        assert current_state.last_file == "new_file.xlsx"
        assert current_state.current_sheet == "Jan 2025"
        assert current_state.current_row == 8  # assuming cursor_position maps to current_row
        assert session_manager._is_dirty is True
        assert isinstance(current_state.last_modified, datetime)
    
    def test_batch_state_updates(self):
        """Test batching multiple state updates efficiently."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        
        # Act - Multiple updates in sequence
        session_manager.update_state(current_file="file1.xlsx")
        session_manager.update_state(current_sheet="Sheet1")
        session_manager.update_state(current_cluster=3)
        
        # Assert - All updates should be reflected
        current_state = session_manager.current_state
        assert current_state.last_file == "file1.xlsx"
        assert current_state.current_sheet == "Sheet1"
        assert current_state.current_cluster == 3
        assert session_manager._is_dirty is True
    
    def test_no_change_updates_keep_clean_state(self):
        """Test that updates with no actual changes don't mark state as dirty."""
        # Arrange
        initial_session = SessionState(
            last_file="test.xlsx",
            current_sheet="Sheet1",
            current_cluster=1
        )
        
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        session_manager._is_dirty = False  # Reset dirty flag
        
        # Act - Update with same values
        session_manager.update_state(
            current_file="test.xlsx",
            current_sheet="Sheet1"
        )
        
        # Assert - Should not be marked dirty
        assert session_manager._is_dirty is False


class TestCheckpointAndSaving:
    """Test manual checkpoint and force save functionality."""
    
    def test_checkpoint_saves_immediately(self):
        """Test that checkpoint forces immediate state save."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        mock_state_io.save_session.return_value = True
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        session_manager.update_state(current_file="test.xlsx")
        
        # Act
        session_manager.checkpoint()
        
        # Assert
        mock_state_io.save_session.assert_called_once()
        assert session_manager._is_dirty is False
        assert session_manager._last_save_time > 0
    
    def test_checkpoint_with_no_changes_skips_save(self):
        """Test that checkpoint skips save when no changes exist."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        # Don't make any changes, state should be clean
        
        # Act
        session_manager.checkpoint()
        
        # Assert - Should not call save_session when no changes
        mock_state_io.save_session.assert_not_called()


class TestAutoSaveLogic:
    """Test automatic save timing and dirty state detection."""
    
    def test_auto_save_respects_interval_timing(self):
        """Test that auto-save respects configured interval settings."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io, auto_save_interval=2)  # 2 seconds
        session_manager.start_session()
        session_manager.update_state(current_file="test.xlsx")
        
        # Act & Assert - Should need auto-save immediately after changes
        assert session_manager.should_auto_save() is True
        
        # Save and reset timer
        session_manager.checkpoint()
        assert session_manager.should_auto_save() is False
        
        # Wait less than interval
        time.sleep(1)
        session_manager.update_state(current_sheet="Sheet1")  # Make it dirty again
        assert session_manager.should_auto_save() is False  # Still within interval
        
        # Wait for full interval
        time.sleep(2)
        assert session_manager.should_auto_save() is True  # Now should auto-save
    
    def test_dirty_state_detection_for_auto_save(self):
        """Test that auto-save only triggers when state changes exist."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io, auto_save_interval=0.1)  # 100ms
        session_manager.start_session()
        
        # Act & Assert - Clean state should not auto-save
        time.sleep(0.2)  # Wait longer than interval
        assert session_manager.should_auto_save() is False
        
        # Make changes and test dirty detection
        session_manager.update_state(current_file="dirty.xlsx")
        assert session_manager.should_auto_save() is True  # Now dirty and time passed
    
    @patch('threading.Timer')
    def test_non_blocking_auto_save_operations(self, mock_timer):
        """Test that auto-save operations don't block the main thread."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        mock_state_io.save_session.return_value = True
        
        # Mock a slow save operation
        def slow_save(state):
            time.sleep(0.1)  # Simulate slow I/O
            return True
        mock_state_io.save_session.side_effect = slow_save
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        session_manager.update_state(current_file="test.xlsx")
        
        # Act - Start checkpoint operation
        start_time = time.time()
        session_manager.checkpoint()
        end_time = time.time()
        
        # Assert - Operation should complete quickly (non-blocking pattern)
        # Note: Actual implementation should use background thread for saves
        assert (end_time - start_time) < 0.05  # Should return quickly


class TestRecoveryMechanisms:
    """Test session recovery from various failure scenarios."""
    
    def test_corrupted_state_recovery(self):
        """Test graceful handling of corrupted session files."""
        # Arrange
        mock_state_io = Mock(spec=StateIO)
        # Simulate corrupted state by returning default session
        mock_state_io.load_session.return_value = SessionState(
            last_file="", 
            current_sheet="", 
            current_cluster=0
        )
        
        # Act
        session_manager = SessionManager(mock_state_io)
        recovered_session = session_manager.start_session()
        
        # Assert - Should get default session without crashing
        assert recovered_session is not None
        assert recovered_session.last_file == ""
        assert recovered_session.current_sheet == ""
        assert recovered_session.current_cluster == 0
        mock_state_io.load_session.assert_called_once()
    
    def test_missing_session_file_recovery(self):
        """Test creating new session when no session file exists."""
        # Arrange
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = SessionState(
            last_file="", 
            current_sheet="", 
            current_cluster=0
        )
        
        # Act
        session_manager = SessionManager(mock_state_io)
        new_session = session_manager.start_session()
        
        # Assert
        assert new_session is not None
        assert new_session.last_file == ""
        assert isinstance(new_session.last_modified, datetime)
        mock_state_io.load_session.assert_called_once()
    
    def test_session_end_cleanup_with_final_save(self):
        """Test proper shutdown cleanup with final state save."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        mock_state_io.save_session.return_value = True
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        session_manager.update_state(current_file="final.xlsx")
        
        # Act
        session_manager.end_session()
        
        # Assert
        mock_state_io.save_session.assert_called_once()
        # After end_session, auto-save timer should be stopped
        assert hasattr(session_manager, '_shutdown_requested')


class TestEditHistoryManagement:
    """Test edit tracking and history management for undo/redo functionality."""
    
    def test_edit_history_tracking(self):
        """Test that edit records are properly tracked and managed."""
        # Arrange  
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        
        # Act - Record some edits
        edit1 = EditRecord(
            timestamp=datetime.now(),
            sheet="Sheet1",
            row=5,
            column="VIEW",
            old_value=100.0,
            new_value=120.0,
            cluster_id=1
        )
        
        edit2 = EditRecord(
            timestamp=datetime.now(),
            sheet="Sheet1", 
            row=6,
            column="PREV",
            old_value=90.0,
            new_value=95.0,
            cluster_id=1
        )
        
        session_manager.record_edit(edit1)
        session_manager.record_edit(edit2)
        
        # Assert
        history = session_manager.get_edit_history()
        assert len(history) == 2
        assert history[0] == edit1
        assert history[1] == edit2
    
    def test_edit_history_memory_management(self):
        """Test that edit history respects memory limits and prunes old entries."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        session_manager = SessionManager(mock_state_io, max_history_entries=3)
        session_manager.start_session()
        
        # Act - Add more edits than max allowed
        for i in range(5):
            edit = EditRecord(
                timestamp=datetime.now(),
                sheet="Sheet1",
                row=i,
                column="VIEW",
                old_value=100.0 + i,
                new_value=120.0 + i,
                cluster_id=1
            )
            session_manager.record_edit(edit)
        
        # Assert - Should only keep the most recent 3 edits
        history = session_manager.get_edit_history()
        assert len(history) == 3
        assert history[0].row == 2  # First kept edit (index 2 from original)
        assert history[2].row == 4  # Last edit (index 4 from original)


class TestPerformanceRequirements:
    """Test performance requirements for SessionManager operations."""
    
    def test_session_load_performance(self):
        """Test that session loading completes within 100ms requirement."""
        # Arrange
        initial_session = SessionState(
            last_file="large_file.xlsx",
            current_sheet="Complex Sheet",
            current_cluster=100
        )
        
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        
        # Act & Assert
        start_time = time.time()
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert load_time < 100, f"Session load took {load_time:.2f}ms, exceeds 100ms requirement"
    
    def test_auto_save_performance(self):
        """Test that auto-save completes within 50ms requirement."""
        # Arrange
        initial_session = SessionState(last_file="", current_sheet="", current_cluster=0)
        mock_state_io = Mock(spec=StateIO)
        mock_state_io.load_session.return_value = initial_session
        mock_state_io.save_session.return_value = True
        
        session_manager = SessionManager(mock_state_io)
        session_manager.start_session()
        session_manager.update_state(current_file="perf_test.xlsx")
        
        # Act & Assert
        start_time = time.time()
        session_manager.checkpoint()
        end_time = time.time()
        
        save_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert save_time < 50, f"Auto-save took {save_time:.2f}ms, exceeds 50ms requirement"