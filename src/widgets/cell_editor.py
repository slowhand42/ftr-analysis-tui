"""Cell editor widget for inline editing of table cells."""

from textual.widgets import Input
from textual.containers import Container
from textual.app import ComposeResult
from textual import events
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class CellEditor(Container):
    """
    Overlay widget for editing cell values.
    
    Appears on top of the cell being edited and handles input validation.
    """
    
    DEFAULT_CSS = """
    CellEditor {
        layer: overlay;
        background: $surface;
        border: solid $primary;
        padding: 0;
        width: auto;
        height: 3;
    }
    
    CellEditor Input {
        width: 20;
        background: white;
        color: black;
    }
    """
    
    def __init__(
        self,
        initial_value: str = "",
        column_name: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        Initialize cell editor.
        
        Args:
            initial_value: Initial value to show in input
            column_name: Name of column being edited (for validation)
            on_submit: Callback when value is submitted
            on_cancel: Callback when editing is cancelled
        """
        super().__init__(**kwargs)
        self.initial_value = initial_value
        self.column_name = column_name
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.input = None
        
    def compose(self) -> ComposeResult:
        """Create the input widget."""
        self.input = Input(
            value=self.initial_value,
            placeholder=f"Enter {self.column_name} value"
        )
        yield self.input
        
    def on_mount(self) -> None:
        """Focus the input when mounted."""
        if self.input:
            self.input.focus()
            # Move cursor to end of initial value
            self.input.cursor_position = len(self.initial_value)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if self.input:
            value = self.input.value.strip()
            
            # Basic validation based on column type
            if self.column_name == "VIEW":
                # VIEW must be positive
                try:
                    float_val = float(value)
                    if float_val <= 0:
                        self.app.notify("VIEW must be positive", severity="error")
                        return
                except ValueError:
                    self.app.notify("Invalid number", severity="error")
                    return
                    
            elif self.column_name in ["SHORTLIMIT", "SHORTLIMIT*"]:
                # SHORTLIMIT must be negative or empty
                if value:  # Allow empty values
                    try:
                        float_val = float(value)
                        if float_val >= 0:
                            self.app.notify("SHORTLIMIT must be negative", severity="error")
                            return
                    except ValueError:
                        self.app.notify("Invalid number", severity="error")
                        return
            
            # Call submit callback
            if self.on_submit_callback:
                self.on_submit_callback(value)
            
            # Remove this widget
            self.remove()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "escape":
            # Cancel editing
            if self.on_cancel_callback:
                self.on_cancel_callback()
            self.remove()
            event.stop()