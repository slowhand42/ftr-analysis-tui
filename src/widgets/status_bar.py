"""StatusBar widget for displaying application status and help."""

from textual.widgets import Static
from textual.reactive import reactive
from rich.console import RenderableType
from rich.text import Text
from typing import Optional
from datetime import datetime


class StatusBar(Static):
    """
    Widget for displaying status information and keyboard shortcuts.

    Shows context-sensitive help and current state information.
    """

    # Reactive properties for position tracking
    current_sheet: str = reactive("SEP25")
    current_cluster: int = reactive(0)
    total_clusters: int = reactive(0)
    current_row: int = reactive(0)
    total_rows: int = reactive(0)

    # Reactive properties for file information
    file_name: str = reactive("")
    is_modified: bool = reactive(False)
    last_save: Optional[datetime] = reactive(None)

    # Reactive properties for edit mode
    edit_mode: bool = reactive(False)
    edit_column: str = reactive("")

    # Reactive property for temporary messages
    message: str = reactive("")

    def __init__(self, **kwargs):
        """Initialize StatusBar."""
        super().__init__(**kwargs)
        self.status_text = ""
        self.help_text = "[n/p] Clusters | [Tab/Shift+Tab] Sheets | [↑↓] Rows | [0-9] Edit | [Ctrl+S] Save | [Ctrl+Q] Quit"
        self.comment_text = ""

    def render(self) -> RenderableType:
        """Render the status bar with position, file info, and help text."""
        left = self._build_position_text()
        center = self._build_file_text()
        right = self._build_help_text()

        # Build combined text with proper spacing
        combined = Text()
        combined.append(left.plain)

        if center.plain:
            combined.append(" | ")
            combined.append(center.plain)

        combined.append(" | ")
        combined.append(right.plain)

        return combined

    def update_status(self, status: str) -> None:
        """
        Update status text.

        Args:
            status: New status text
        """
        self.status_text = status
        self.refresh()

    def set_status(self, status: str) -> None:
        """
        Set status text (alias for update_status for compatibility).

        Args:
            status: New status text
        """
        self.update_status(status)

    def show_comment(self, comment: str) -> None:
        """
        Show a comment in the status bar.

        Args:
            comment: Comment text to display
        """
        self.comment_text = comment
        self.refresh()

    def clear_comment(self) -> None:
        """Clear the comment text."""
        self.comment_text = ""
        self.refresh()

    def update_help(self, help_text: str) -> None:
        """
        Update help text based on context.

        Args:
            help_text: New help text
        """
        self.help_text = help_text
        self.refresh()

    def show_edit_mode(self, column: str) -> None:
        """
        Show edit mode help.

        Args:
            column: Column being edited
        """
        self.status_text = f"Editing {column}"
        self.help_text = "[Enter] Save & Next | [Tab] Save & Switch | [Esc] Cancel"
        self.refresh()

    def show_normal_mode(self) -> None:
        """Show normal mode help."""
        self.status_text = ""
        self.help_text = ("[n/p] Clusters | [Tab/Shift+Tab] Sheets | "
                          "[↑↓] Rows | [0-9] Edit | [Ctrl+S] Save | [Ctrl+Q] Quit")
        self.refresh()

    def update_position(self, sheet: str, cluster: int, row: int, total_rows: int) -> None:
        """Update position information."""
        self.current_sheet = sheet
        self.current_cluster = cluster
        self.current_row = row
        self.total_rows = total_rows

    def set_file_info(self, file_name: str, modified: bool = False) -> None:
        """Update file information."""
        self.file_name = self._truncate_filename(file_name)
        self.is_modified = modified

    def set_edit_mode(self, editing: bool, column: str = "") -> None:
        """Update edit mode status."""
        self.edit_mode = editing
        self.edit_column = column

    def show_message(self, message: str, duration: float = 3.0) -> None:
        """Display temporary message."""
        self.message = message
        # Note: Duration handling would be implemented with a timer in real app

    def show_hint(self, hint: str) -> None:
        """Display a temporary hint message."""
        self.message = hint
        self.refresh()

    def _build_position_text(self) -> Text:
        """Build position section."""
        text = Text()
        text.append(f"{self.current_sheet} | ")
        text.append(f"Cluster {self.current_cluster}/{self.total_clusters} | ")
        text.append(f"Row {self.current_row}/{self.total_rows}")
        if self.edit_mode:
            text.append(f" | Editing: {self.edit_column}")
        return text

    def _build_file_text(self) -> Text:
        """Build file info section."""
        text = Text()
        if self.file_name:
            text.append(self.file_name)
            if self.is_modified:
                text.append(" *")
            if self.last_save:
                save_time = self.last_save.strftime("%H:%M:%S")
                text.append(f" | Saved: {save_time}")
        return text

    def _build_help_text(self) -> Text:
        """Build help text section."""
        if self.edit_mode:
            return Text("[Enter] Save | [Esc] Cancel | [Tab] Next Field")
        else:
            return Text("[n/p] Clusters | [Tab/Shift+Tab] Sheets | [↑↓] Rows | [0-9] Edit | [Ctrl+S] Save | [Ctrl+Q] Quit")

    def _truncate_filename(self, filename: str, max_len: int = 30) -> str:
        """Truncate long filenames."""
        if len(filename) <= max_len:
            return filename
        return "..." + filename[-(max_len - 3):]
