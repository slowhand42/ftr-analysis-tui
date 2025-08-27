"""Session state management for persistence between runs."""

import logging
from typing import Optional
from pathlib import Path

from ..models import SessionState
from ..io import StateIO


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages persistent session state between application runs.
    
    State includes:
    - Current sheet
    - Current cluster
    - Row position
    - Window size
    """
    
    DEFAULT_STATE_FILE = ".analysis-tui-state.json"
    
    def __init__(self, state_io: Optional[StateIO] = None):
        """Initialize session manager."""
        self.state_io = state_io or StateIO()
        self.current_state: Optional[SessionState] = None
        self.state_file_path: Optional[Path] = None
    
    def save_state(self, state: SessionState) -> None:
        """
        Save session state to file.
        
        Args:
            state: SessionState to save
        """
        if not self.state_file_path:
            logger.warning("No state file path set, cannot save state")
            return
        
        try:
            self.state_io.save_json(state.to_dict(), str(self.state_file_path))
            self.current_state = state
            logger.debug(f"Saved session state to {self.state_file_path}")
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
    
    def load_state(self) -> Optional[SessionState]:
        """
        Load session state from file.
        
        Returns:
            SessionState if found and valid, None otherwise
        """
        if not self.state_file_path or not self.state_file_path.exists():
            logger.debug("No state file found")
            return None
        
        try:
            data = self.state_io.load_json(str(self.state_file_path))
            state = SessionState.from_dict(data)
            self.current_state = state
            logger.debug(f"Loaded session state from {self.state_file_path}")
            return state
        except Exception as e:
            logger.error(f"Failed to load session state: {e}")
            return None
    
    def clear_state(self) -> None:
        """Clear current state and delete state file."""
        if self.state_file_path and self.state_file_path.exists():
            try:
                self.state_file_path.unlink()
                logger.debug("Deleted state file")
            except Exception as e:
                logger.error(f"Failed to delete state file: {e}")
        
        self.current_state = None
    
    def set_state_file_location(self, excel_file_path: str) -> None:
        """
        Set state file location based on Excel file path.
        
        The state file will be created in the same directory as the Excel file.
        
        Args:
            excel_file_path: Path to the Excel file
        """
        excel_path = Path(excel_file_path)
        self.state_file_path = excel_path.parent / self.DEFAULT_STATE_FILE
        logger.debug(f"State file location set to: {self.state_file_path}")
    
    def update_current_state(self, **kwargs) -> None:
        """
        Update specific fields in current state.
        
        Args:
            **kwargs: Fields to update (e.g., current_sheet="SEP25")
        """
        if not self.current_state:
            logger.warning("No current state to update")
            return
        
        for key, value in kwargs.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
            else:
                logger.warning(f"Unknown state field: {key}")
        
        # Auto-save on update
        self.save_state(self.current_state)
    
    def get_or_create_state(self, excel_file: str, default_sheet: str = "SEP25") -> SessionState:
        """
        Get existing state or create new one.
        
        Args:
            excel_file: Path to Excel file
            default_sheet: Default sheet to use
            
        Returns:
            SessionState (loaded or newly created)
        """
        self.set_state_file_location(excel_file)
        
        # Try to load existing state
        state = self.load_state()
        
        if state and state.last_file == excel_file:
            # Valid state for this file
            return state
        
        # Create new state
        state = SessionState(
            last_file=excel_file,
            current_sheet=default_sheet,
            current_cluster=0,
            current_row=0
        )
        
        self.current_state = state
        self.save_state(state)
        return state