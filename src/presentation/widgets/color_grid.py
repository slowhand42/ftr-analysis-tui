"""ColorGrid Textual widget for colored grid display of constraint data."""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message

from ...business_logic.color_formatter import ColorFormatter


class CellSelected(Message):
    """Emitted when user selects a cell."""

    def __init__(self, row: int, col: int, value: Any):
        self.row = row
        self.col = col
        self.value = value
        super().__init__()


class CellHovered(Message):
    """Emitted when mouse hovers over cell."""

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        super().__init__()


class ColorGrid(Static):
    """Colored grid display for constraint data using block characters."""

    data = reactive(pd.DataFrame, always_update=True)
    column_type = reactive(str)
    focused_cell = reactive((0, 0))

    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        column_type: str = "VIEW",
        color_formatter: Optional[ColorFormatter] = None,
        **kwargs
    ):
        """
        Initialize ColorGrid.

        Args:
            data: DataFrame with constraint data
            column_type: Type of column (VIEW, PREV, etc.)
            color_formatter: ColorFormatter for color calculations
        """
        super().__init__(**kwargs)
        self.data = data if data is not None else pd.DataFrame()
        self.column_type = column_type
        self.color_formatter = color_formatter or ColorFormatter()
        self.focused_cell = (0, 0)

    def render(self) -> str:
        """Render the colored grid using block characters."""
        if self.data.empty:
            return ""

        lines = []

        # Render grid row by row
        for row_idx, (row_name, row_data) in enumerate(self.data.iterrows()):
            row_chars = []

            # Render cells in row
            for col_idx, (col_name, value) in enumerate(row_data.items()):
                # Choose block character based on value
                block_char = self._get_block_char(value)
                row_chars.append(block_char)

            lines.append(''.join(row_chars))

        return '\n'.join(lines)

    def _get_cell_color(self, value: Any) -> str:
        """Get hex color for cell value based on column type."""
        if pd.isna(value) or value is None:
            return "#CCCCCC"  # Neutral gray for missing values

        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return "#CCCCCC"  # Gray for invalid values

        if self.column_type == "VIEW":
            return self.color_formatter.get_view_color(float_value)
        elif self.column_type == "PREV":
            return self.color_formatter.get_prev_color(float_value)
        else:
            return self.color_formatter.get_view_color(float_value)

    def _get_block_char(self, value: Any) -> str:
        """Get block character based on value magnitude."""
        if pd.isna(value) or value is None:
            return "░"  # Light block for missing values

        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return "░"  # Light block for invalid values

        # Use different block characters based on value ranges
        abs_value = abs(float_value)
        if abs_value >= 200:
            return "█"  # Full block for high values
        elif abs_value >= 100:
            return "▓"  # Dark shade
        elif abs_value >= 50:
            return "▒"  # Medium shade
        else:
            return "░"  # Light shade

    def get_cell_info(self, row: int, col: int) -> Dict[str, Any]:
        """Get information about a specific cell for tooltips."""
        if self.data.empty:
            return {}

        try:
            if row >= len(self.data) or col >= len(self.data.columns):
                return {}

            row_name = self.data.index[row]
            col_name = self.data.columns[col]
            value = self.data.iloc[row, col]

            return {
                'value': value,
                'constraint': row_name,
                'row_name': row_name,
                'column': col_name,
                'date': col_name
            }
        except (IndexError, KeyError):
            return {}

    def watch_data(self, old_data: pd.DataFrame, new_data: pd.DataFrame) -> None:
        """React to data changes."""
        self.refresh()

    def watch_column_type(self, old_type: str, new_type: str) -> None:
        """React to column type changes."""
        self.refresh()

    def watch_focused_cell(self, old_cell: Tuple[int, int], new_cell: Tuple[int, int]) -> None:
        """React to focused cell changes."""
        # Clamp coordinates to valid ranges
        if not self.data.empty:
            max_row = len(self.data) - 1
            max_col = len(self.data.columns) - 1

            row, col = new_cell
            row = max(0, min(row, max_row))
            col = max(0, min(col, max_col))

            if (row, col) != new_cell:
                self.focused_cell = (row, col)
                return

        self.refresh()
