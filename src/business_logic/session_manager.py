"""SessionManager for coordinating session state persistence and auto-save functionality."""

import time
import threading
from datetime import datetime
from typing import Optional, List
from collections import deque

from src.io.state_io import StateIO
from src.models.data_models import SessionState, EditRecord


class SessionManager:
    """
    Manages session state persistence, auto-save functionality, and edit history.

    Coordinates state updates, dirty tracking, and provides recovery mechanisms
    for maintaining application state across sessions.
    """

    def __init__(self, state_io: StateIO, auto_save_interval: int = 60,
                 max_history_entries: int = 100):
        """
        Initialize SessionManager with StateIO dependency injection.

        Args:
            state_io: StateIO instance for persistence operations
            auto_save_interval: Auto-save interval in seconds (default: 60)
            max_history_entries: Maximum edit history entries to maintain (default: 100)
        """
        self.state_io = state_io
        self.auto_save_interval = auto_save_interval
        self.max_history_entries = max_history_entries

        self.current_state: Optional[SessionState] = None
        self._is_dirty = False
        self._last_save_time = 0
        self._shutdown_requested = False
        self._has_been_saved = False  # Track if we've ever saved during this session

        # Edit history for undo/redo
        self._edit_history: deque = deque(maxlen=max_history_entries)

        # Threading lock for thread-safe operations
        self._lock = threading.Lock()

    def start_session(self) -> SessionState:
        """
        Load or create session state.

        Returns:
            SessionState object with current session data
        """
        with self._lock:
            # Load session from StateIO
            self.current_state = self.state_io.load_session()

            # Update last_modified timestamp
            self.current_state.last_modified = datetime.now()

            # Mark as clean initially
            self._is_dirty = False
            self._last_save_time = time.time()

            return self.current_state

    def update_state(self, **updates) -> None:
        """
        Update current session state with provided keyword arguments.

        Args:
            **updates: Key-value pairs to update in the session state
        """
        with self._lock:
            if self.current_state is None:
                return

            # Check if any updates actually change the state
            state_changed = False

            for key, value in updates.items():
                # Handle special mappings
                if key == "current_file":
                    if self.current_state.last_file != value:
                        self.current_state.last_file = value
                        state_changed = True
                elif key == "cursor_position":
                    # Assuming cursor_position is (row, col) and we only track row
                    if isinstance(value, (list, tuple)) and len(value) >= 1:
                        if self.current_state.current_row != value[0]:
                            self.current_state.current_row = value[0]
                            state_changed = True
                elif hasattr(self.current_state, key):
                    current_value = getattr(self.current_state, key)
                    if current_value != value:
                        setattr(self.current_state, key, value)
                        state_changed = True

            if state_changed:
                self.current_state.last_modified = datetime.now()
                self._is_dirty = True

    def checkpoint(self) -> None:
        """
        Force immediate state save if there are pending changes.
        """
        with self._lock:
            if self.current_state is None:
                return

            if not self._is_dirty:
                return  # No changes to save

            # Create a copy of the current state for background save
            state_to_save = SessionState(
                last_file=self.current_state.last_file,
                current_sheet=self.current_state.current_sheet,
                current_cluster=self.current_state.current_cluster,
                current_row=self.current_state.current_row,
                window_size=self.current_state.window_size,
                last_modified=self.current_state.last_modified
            )

        # Perform save operation in background thread
        def _background_save():
            if self.state_io.save_session(state_to_save):
                with self._lock:
                    self._is_dirty = False
                    self._last_save_time = time.time()
                    self._has_been_saved = True

        # Start background thread for save operation
        save_thread = threading.Thread(target=_background_save, daemon=True)
        save_thread.start()

    def should_auto_save(self) -> bool:
        """
        Check if auto-save should be triggered based on timing and dirty state.

        Returns:
            True if auto-save should be performed, False otherwise
        """
        with self._lock:
            if not self._is_dirty:
                return False

            # If dirty and no checkpoint saves have been performed yet, should save immediately
            if not self._has_been_saved:
                return True

            time_since_last_save = time.time() - self._last_save_time
            return time_since_last_save >= self.auto_save_interval

    def end_session(self) -> None:
        """
        Clean shutdown with final state save.
        """
        self._shutdown_requested = True

        with self._lock:
            if self.current_state is not None and self._is_dirty:
                self.state_io.save_session(self.current_state)
                self._is_dirty = False

    def record_edit(self, edit_record: EditRecord) -> None:
        """
        Record an edit in the history for undo/redo functionality.

        Args:
            edit_record: EditRecord to add to history
        """
        with self._lock:
            self._edit_history.append(edit_record)

    def get_edit_history(self) -> List[EditRecord]:
        """
        Get the current edit history.

        Returns:
            List of EditRecord objects in chronological order
        """
        with self._lock:
            return list(self._edit_history)
