"""Comprehensive tests for StateIO JSON persistence functionality.

This module tests the StateIO class following TDD methodology.
Tests focus on file I/O operations, error handling, and data integrity.
"""

import json
import os
import tempfile
import shutil
import stat
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

from src.io.state_io import StateIO
from src.models.data_models import SessionState


class TestStateIOCore:
    """Core functionality tests for StateIO."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.state_io = StateIO(session_dir=self.temp_dir)
        self.sample_state = SessionState(
            last_file="test_file.xlsx",
            current_sheet="Sheet1",
            current_cluster=1,
            current_row=5,
            window_size=(100, 50),
            last_modified=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_save_session_creates_json_file(self):
        """Test that save_session creates a JSON file with correct content."""
        # When: saving a session state
        result = self.state_io.save_session(self.sample_state)
        
        # Then: operation should succeed
        assert result is True
        
        # And: JSON file should exist
        session_file = self.temp_dir / "session.json"
        assert session_file.exists()
        
        # And: file should contain correct JSON data
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert data['last_file'] == "test_file.xlsx"
        assert data['current_sheet'] == "Sheet1"
        assert data['current_cluster'] == 1
        assert data['current_row'] == 5
        assert data['window_size'] == [100, 50]
        assert data['last_modified'] == "2024-01-01T12:00:00"
    
    def test_load_session_returns_saved_state(self):
        """Test round-trip save/load verification."""
        # Given: a saved session state
        self.state_io.save_session(self.sample_state)
        
        # When: loading the session
        loaded_state = self.state_io.load_session()
        
        # Then: loaded state should match original
        assert loaded_state.last_file == self.sample_state.last_file
        assert loaded_state.current_sheet == self.sample_state.current_sheet
        assert loaded_state.current_cluster == self.sample_state.current_cluster
        assert loaded_state.current_row == self.sample_state.current_row
        assert loaded_state.window_size == self.sample_state.window_size
        assert loaded_state.last_modified == self.sample_state.last_modified
    
    def test_load_missing_file_returns_default(self):
        """Test handling of non-existent session files."""
        # Given: no session file exists
        assert not (self.temp_dir / "session.json").exists()
        
        # When: loading session
        loaded_state = self.state_io.load_session()
        
        # Then: should return default SessionState
        assert isinstance(loaded_state, SessionState)
        assert loaded_state.last_file == ""
        assert loaded_state.current_sheet == ""
        assert loaded_state.current_cluster == 0
        assert loaded_state.current_row == 0
        assert loaded_state.window_size == (120, 40)
    
    def test_atomic_save_prevents_corruption(self):
        """Test that atomic save uses temp file approach."""
        # Given: existing session file
        session_file = self.temp_dir / "session.json"
        session_file.write_text('{"old": "data"}')
        
        # When: saving with simulated interruption during write
        with patch('builtins.open', mock_open()) as mock_file:
            # Simulate error after temp file created but before rename
            mock_file.side_effect = [mock_open().return_value, OSError("Simulated error")]
            
            result = self.state_io.save_session(self.sample_state)
            
            # Then: save should fail
            assert result is False
            
            # And: original file should remain unchanged
            with open(session_file, 'r') as f:
                data = json.load(f)
            assert data == {"old": "data"}


class TestStateIOErrorHandling:
    """Error handling tests for StateIO."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.state_io = StateIO(session_dir=self.temp_dir)
        self.sample_state = SessionState(
            last_file="test.xlsx",
            current_sheet="Sheet1", 
            current_cluster=1
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handle_corrupted_json_gracefully(self):
        """Test handling of malformed JSON files."""
        # Given: corrupted JSON file
        session_file = self.temp_dir / "session.json"
        session_file.write_text('{"invalid": json, missing quotes}')
        
        # When: loading session
        loaded_state = self.state_io.load_session()
        
        # Then: should return default state (not crash)
        assert isinstance(loaded_state, SessionState)
        assert loaded_state.last_file == ""
    
    def test_permission_errors_handled(self):
        """Test handling of read-only directory."""
        # Given: read-only directory
        if os.name != 'nt':  # Skip on Windows (permission handling different)
            readonly_dir = self.temp_dir / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # r-x------
            
            readonly_state_io = StateIO(session_dir=readonly_dir)
            
            # When: attempting to save
            result = readonly_state_io.save_session(self.sample_state)
            
            # Then: should handle gracefully
            assert result is False
    
    def test_disk_space_error_handling(self):
        """Test graceful failure when disk is full."""
        # When: simulating disk full condition
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            result = self.state_io.save_session(self.sample_state)
            
            # Then: should handle error gracefully
            assert result is False


class TestStateIOFileManagement:
    """File management tests for StateIO."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        # Initialize with non-existent directory to test auto-creation
        self.session_dir = self.temp_dir / "ftr_analysis"
        self.state_io = StateIO(session_dir=self.session_dir)
        self.sample_state = SessionState(
            last_file="test.xlsx",
            current_sheet="Sheet1",
            current_cluster=1
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_session_directory_auto_creation(self):
        """Test automatic creation of session directory."""
        # Given: session directory doesn't exist
        assert not self.session_dir.exists()
        
        # When: saving a session
        result = self.state_io.save_session(self.sample_state)
        
        # Then: directory should be created
        assert result is True
        assert self.session_dir.exists()
        assert (self.session_dir / "session.json").exists()
    
    def test_backup_creation_before_overwrite(self):
        """Test that backup is created before overwriting session."""
        # Given: existing session file
        self.state_io.save_session(self.sample_state)
        
        # When: creating backup
        result = self.state_io.backup_current_session()
        
        # Then: backup should be created
        assert result is True
        
        # And: backup file should exist with timestamp
        backup_files = list(self.session_dir.glob("session_backup_*.json"))
        assert len(backup_files) == 1
        
        # And: backup should contain original data
        with open(backup_files[0], 'r') as f:
            backup_data = json.load(f)
        assert backup_data['last_file'] == "test.xlsx"
    
    def test_backup_rotation_keeps_limit(self):
        """Test that only last N backups are kept."""
        # Given: multiple backup files
        self.state_io.save_session(self.sample_state)
        
        # Create 7 backup files (more than default limit of 5)
        for i in range(7):
            backup_time = datetime.now() - timedelta(days=i)
            backup_name = f"session_backup_{backup_time.strftime('%Y%m%d_%H%M%S')}.json"
            backup_file = self.session_dir / backup_name
            backup_file.write_text('{"test": "data"}')
        
        # When: cleaning old sessions
        deleted_count = self.state_io.clean_old_sessions(keep_count=5)
        
        # Then: should delete excess backups
        assert deleted_count == 2
        
        # And: should keep only 5 most recent
        remaining_backups = list(self.session_dir.glob("session_backup_*.json"))
        assert len(remaining_backups) == 5


class TestStateIODefaultDirectory:
    """Test StateIO with default ~/.ftr_analysis directory."""
    
    def test_default_session_directory_path(self):
        """Test that default directory is ~/.ftr_analysis."""
        # When: creating StateIO without custom directory
        state_io = StateIO()
        
        # Then: should use home directory path
        expected_path = Path.home() / ".ftr_analysis"
        assert state_io.session_dir == expected_path