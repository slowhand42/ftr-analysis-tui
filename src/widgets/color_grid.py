"""ColorGrid widget for displaying date/LODF values as colored blocks."""

from textual.widgets import Static
from textual.reactive import reactive
from rich.console import RenderableType
from rich.text import Text
from rich.style import Style
from typing import List, Dict, Optional, Callable

from ..core.formatter import ColorFormatter
from ..models import GridComment


class ColorGrid(Static):
    """
    Widget for displaying date/LODF values as colored blocks.

    Features:
    - Compact color visualization
    - Comment indicators (dots/asterisks)
    - Hover tooltips for actual values
    """

    selected_index = reactive(-1)

    def __init__(
        self,
        values: Optional[List[float]] = None,
        comments: Optional[Dict[int, GridComment]] = None,
        grid_type: str = "date",  # "date" or "lodf"
        formatter: Optional[ColorFormatter] = None,
        on_hover: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        """
        Initialize ColorGrid.

        Args:
            values: List of values to display
            comments: Dictionary of column index to comments
            grid_type: Type of grid ("date" or "lodf")
            formatter: ColorFormatter for colors
            on_hover: Callback for hover events
        """
        super().__init__(**kwargs)
        self.values = values or []
        self.comments = comments or {}
        self.grid_type = grid_type
        self.formatter = formatter or ColorFormatter()
        self.on_hover_callback = on_hover

    def render(self) -> RenderableType:
        """Render the color grid."""
        text = Text()

        if not self.values:
            text.append("No data", style="dim")
            return text

        # Add label
        label = "Date Grid: " if self.grid_type == "date" else "LODF Grid: "
        text.append(label, style="bold")

        # Render colored blocks
        for i, value in enumerate(self.values):
            # Get color based on value
            if self.grid_type == "date":
                color = self.formatter._get_date_column_color(value)
            else:  # lodf
                color = self.formatter._get_lodf_color(value)

            # Create block character
            block_char = "█"

            # Add comment indicator if present
            if i in self.comments:
                if self.comments[i].is_outage:
                    block_char = "*"  # Asterisk for outage
                else:
                    block_char = "•"  # Dot for other comments

            # Apply color and add to text
            style = Style(color=color)
            text.append(block_char, style=style)

            # Add spacing between groups of 10
            if (i + 1) % 10 == 0 and i < len(self.values) - 1:
                text.append(" ")

        return text

    def render_grid(self, values: List[float], comments: Dict[int, GridComment]) -> None:
        """
        Update and render grid with new values.

        Args:
            values: New values to display
            comments: New comments dictionary
        """
        self.values = values
        self.comments = comments
        self.refresh()

    def show_comment(self, index: int) -> Optional[str]:
        """
        Get comment text for a specific index.

        Args:
            index: Column index

        Returns:
            Comment text if exists
        """
        if index in self.comments:
            return self.comments[index].comment_text
        return None

    def on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse hover to show tooltips."""
        # Calculate which cell is being hovered
        # Account for label and spacing
        label_len = 11  # "Date Grid: " or "LODF Grid: "

        if x < label_len:
            return

        # Calculate index accounting for spacing
        adjusted_x = x - label_len
        # Account for spaces every 10 blocks
        groups = adjusted_x // 11
        remainder = adjusted_x % 11

        if remainder == 10:  # On a space
            return

        index = groups * 10 + remainder

        if 0 <= index < len(self.values):
            self.selected_index = index
            if self.on_hover_callback:
                self.on_hover_callback(index)

    def get_value_at_index(self, index: int) -> Optional[float]:
        """
        Get the value at a specific index.

        Args:
            index: Grid index

        Returns:
            Value at index or None
        """
        if 0 <= index < len(self.values):
            return self.values[index]
        return None
