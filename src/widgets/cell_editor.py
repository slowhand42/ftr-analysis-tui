"""Cell editor widget for inline editing of table cells."""

from textual.widgets import Input
from textual.containers import Container
from textual.app import ComposeResult
from textual import events
from typing import Optional, Callable


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
        background: $boost;
        color: $text;
        border: solid $accent;
    }
    """
    
    def __init__(
        self,
        initial_value: str = "",
        column_name: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        parent_view: Optional[object] = None,
        **kwargs
    ):
        """
        Initialize cell editor.
        
        Args:
            initial_value: Initial value to show in input
            column_name: Name of column being edited (for validation)
            on_submit: Callback when value is submitted
            on_cancel: Callback when editing is cancelled
            parent_view: Reference to parent view (for accessing keystroke buffer)
        """
        super().__init__(**kwargs)
        self.initial_value = initial_value
        self.column_name = column_name
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.parent_view = parent_view
        self.input = None
        
    def compose(self) -> ComposeResult:
        """Create the input widget."""
        # Create input with initial value if provided
        self.input = Input(
            value=self.initial_value if self.initial_value else "",
            placeholder=f"Enter {self.column_name} value"
        )
        yield self.input
        
    def on_mount(self) -> None:
        """Focus the input when mounted."""
        if self.input:
            # Immediately focus and place cursor at end to avoid select-all replacing text.
            try:
                self.input.focus()
                if self.input.value is not None:
                    cursor_pos = len(self.input.value)
                    self.input.cursor_position = cursor_pos
                    self.input.selection = (cursor_pos, cursor_pos)
            except Exception:
                pass

            # Also run after refresh to reinforce the cursor position once rendered
            def setup_input_after_refresh():
                try:
                    self.input.focus()
                    if self.input.value is not None:
                        cursor_pos = len(self.input.value)
                        self.input.cursor_position = cursor_pos
                        self.input.selection = (cursor_pos, cursor_pos)
                except Exception:
                    pass
            self.call_after_refresh(setup_input_after_refresh)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if self.input:
            value = self.input.value.strip()
            
            # Validate the value
            if self._validate_value(value):
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
        elif event.key in ["up", "down", "left", "right"]:
            # Cancel editing and allow navigation
            if self.on_cancel_callback:
                self.on_cancel_callback()
            self.remove()
            # Let the event continue for navigation
            return
    
    def _validate_value(self, value: str) -> bool:
        """Validate the input value based on column type."""
        if not value:
            return True  # Allow empty values
            
        try:
            float_val = float(value)
            
            if self.column_name == "VIEW":
                if float_val <= 0:
                    self.app.notify("VIEW must be positive", severity="error")
                    return False
                    
            elif self.column_name in ["SHORTLIMIT", "SHORTLIMIT*"]:
                if float_val >= 0:
                    self.app.notify("SHORTLIMIT must be negative", severity="error")
                    return False
            
            return True
        except ValueError:
            self.app.notify("Invalid number", severity="error")
            return False
