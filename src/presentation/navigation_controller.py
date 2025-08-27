"""Navigation controller for coordinated navigation across the TUI."""

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ..app import AnalysisTUIApp


class NavigationController:
    """
    Controller for coordinated navigation across the TUI application.
    
    Manages cursor position, navigation history, and provides advanced
    navigation features like quick jump and undo.
    """
    
    def __init__(self, app: 'AnalysisTUIApp'):
        """
        Initialize the navigation controller.
        
        Args:
            app: Reference to the main TUI application
        """
        self.app = app
        self.current_row = 0
        self.current_col = 0
        self.navigation_history: List[Tuple[str, int, int, int]] = []  # (sheet, cluster, row, col)
        self.max_history = 50
        
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get current cursor position.
        
        Returns:
            Tuple of (row, column) position
        """
        return (self.current_row, self.current_col)
    
    def move_cursor(self, dx: int, dy: int) -> bool:
        """
        Move cursor by delta amounts.
        
        Args:
            dx: Column delta
            dy: Row delta
            
        Returns:
            True if movement was successful, False if blocked
        """
        new_row = max(0, self.current_row + dy)
        new_col = max(0, self.current_col + dx)
        
        # Boundary checking would go here based on current cluster data
        # For now, simple movement without bounds checking
        self.current_row = new_row
        self.current_col = new_col
        
        return True
    
    def navigate_cluster(self, direction: int) -> bool:
        """
        Navigate to next/previous cluster with wrap-around.
        
        Args:
            direction: 1 for forward, -1 for backward
            
        Returns:
            True if navigation successful
        """
        if not self.app.current_cluster_list:
            return False
        
        # Record current position in history
        self._record_navigation()
        
        # Calculate new index with wrap-around
        current_idx = self.app.current_cluster_index
        cluster_count = len(self.app.current_cluster_list)
        
        if direction > 0:  # Forward
            new_idx = (current_idx + 1) % cluster_count
        else:  # Backward
            new_idx = (current_idx - 1) % cluster_count
        
        # Update app state
        self.app.current_cluster_index = new_idx
        self.app.display_current_cluster()
        
        return True
    
    def goto_cluster(self, cluster_id: str) -> bool:
        """
        Jump directly to a specific cluster by ID.
        
        Args:
            cluster_id: Target cluster identifier
            
        Returns:
            True if cluster found and navigation successful
        """
        if cluster_id in self.app.current_cluster_list:
            # Record current position in history
            self._record_navigation()
            
            # Navigate to target cluster
            target_index = self.app.current_cluster_list.index(cluster_id)
            self.app.current_cluster_index = target_index
            self.app.display_current_cluster()
            
            return True
        
        return False
    
    def get_navigation_history(self) -> List[Tuple[str, int, int, int]]:
        """
        Get navigation history.
        
        Returns:
            List of (sheet, cluster_index, row, col) tuples
        """
        return self.navigation_history.copy()
    
    def undo_navigation(self) -> bool:
        """
        Undo the last navigation operation.
        
        Returns:
            True if undo was successful
        """
        if not self.navigation_history:
            return False
        
        # Pop the last position
        last_sheet, last_cluster_idx, last_row, last_col = self.navigation_history.pop()
        
        # Restore position
        if (last_sheet == self.app.sheet_tabs.active_sheet and 
            0 <= last_cluster_idx < len(self.app.current_cluster_list)):
            
            self.app.current_cluster_index = last_cluster_idx
            self.current_row = last_row
            self.current_col = last_col
            self.app.display_current_cluster()
            
            return True
        
        return False
    
    def _record_navigation(self) -> None:
        """Record current navigation position in history."""
        if not self.app.sheet_tabs or not self.app.current_cluster_list:
            return
        
        current_position = (
            self.app.sheet_tabs.active_sheet,
            self.app.current_cluster_index,
            self.current_row,
            self.current_col
        )
        
        # Add to history, maintaining max size
        self.navigation_history.append(current_position)
        if len(self.navigation_history) > self.max_history:
            self.navigation_history.pop(0)