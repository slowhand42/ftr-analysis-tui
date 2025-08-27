"""JSON state file I/O operations with session management."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from src.models.data_models import SessionState

logger = logging.getLogger(__name__)


class StateIO:
    """
    Handles session state persistence with atomic JSON operations.
    
    Provides session state saving/loading with backup rotation and error handling.
    """
    
    def __init__(self, session_dir: Optional[Path] = None):
        """
        Initialize StateIO with session directory.
        
        Args:
            session_dir: Directory for session files. Defaults to ~/.ftr_analysis
        """
        if session_dir is None:
            self.session_dir = Path.home() / ".ftr_analysis"
        else:
            self.session_dir = Path(session_dir)
    
    def save_session(self, session_state: SessionState) -> bool:
        """
        Save session state to JSON file atomically.
        
        Args:
            session_state: SessionState object to save
            
        Returns:
            True if save succeeded, False otherwise
        """
        temp_file_path = None
        try:
            # Ensure directory exists
            self.session_dir.mkdir(parents=True, exist_ok=True)
            
            session_file = self.session_dir / "session.json"
            temp_file_path = session_file.with_suffix('.tmp')
            
            # Write to temporary file first (atomic operation)
            with open(temp_file_path, 'w') as temp_file:
                json.dump(session_state.to_dict(), temp_file, indent=2)
            
            # Verify write by reading back (needed for certain test scenarios)
            with open(temp_file_path, 'r') as verify_file:
                json.load(verify_file)
            
            # Atomic rename
            os.rename(temp_file_path, session_file)
            logger.debug(f"Saved session to {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            # Clean up temp file if it exists
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except (OSError, PermissionError):
                    pass
            return False
    
    def load_session(self) -> SessionState:
        """
        Load session state from JSON file.
        
        Returns:
            SessionState object, or default SessionState if load fails
        """
        session_file = self.session_dir / "session.json"
        
        if not session_file.exists():
            logger.debug("No session file found, returning default state")
            return SessionState(last_file="", current_sheet="", current_cluster=0)
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            session_state = SessionState.from_dict(data)
            logger.debug(f"Loaded session from {session_file}")
            return session_state
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Corrupted or invalid session file: {e}, returning default state")
            return SessionState(last_file="", current_sheet="", current_cluster=0)
        except Exception as e:
            logger.error(f"Failed to load session: {e}, returning default state")
            return SessionState(last_file="", current_sheet="", current_cluster=0)
    
    def backup_current_session(self) -> bool:
        """
        Create backup of current session file.
        
        Returns:
            True if backup created successfully, False otherwise
        """
        session_file = self.session_dir / "session.json"
        
        if not session_file.exists():
            logger.debug("No session file to backup")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"session_backup_{timestamp}.json"
            backup_file = self.session_dir / backup_name
            
            # Copy session file to backup
            with open(session_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
            
            logger.debug(f"Created backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def clean_old_sessions(self, keep_count: int = 5) -> int:
        """
        Clean old backup files, keeping only the most recent ones.
        
        Args:
            keep_count: Number of backup files to keep
            
        Returns:
            Number of files deleted
        """
        try:
            # Find all backup files
            backup_files = list(self.session_dir.glob("session_backup_*.json"))
            
            if len(backup_files) <= keep_count:
                return 0
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Delete old files beyond keep_count
            files_to_delete = backup_files[keep_count:]
            deleted_count = 0
            
            for backup_file in files_to_delete:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete {backup_file}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to clean old sessions: {e}")
            return 0