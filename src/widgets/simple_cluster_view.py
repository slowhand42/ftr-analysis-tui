"""Simple ClusterView widget that displays data in a table format."""

from textual.widgets import DataTable
from rich.text import Text
from typing import Optional, Dict, Any
import pandas as pd
import logging
from ..core.formatter import ColorFormatter
from ..models import ColumnType
from .cell_editor import CellEditor

logger = logging.getLogger(__name__)


class SimpleClusterView(DataTable):
    """Simplified cluster view that just displays data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.show_header = True
        self.zebra_stripes = True
        self.cursor_type = "cell"
        self._data_loaded = False
        self.formatter = ColorFormatter()
        # Map column names to ColumnType for formatting
        self.column_type_map = {
            'VIEW': ColumnType.VIEW,
            'PREV (SEP25)': ColumnType.PREV,
            'PACTUAL': ColumnType.PACTUAL,
            'PEXPECTED': ColumnType.PEXPECTED,
            'VIEWLG': ColumnType.VIEWLG,
            'CSP95': ColumnType.CSP95,
            'CSP80': ColumnType.CSP80,
            'CSP50': ColumnType.CSP50,
            'CSP20': ColumnType.CSP20,
            'CSP5': ColumnType.CSP5,
            'SP': ColumnType.SP,
            'RECENT_DELTA': ColumnType.RECENT_DELTA,
            'FLOW': ColumnType.FLOW,
        }
        # Disable DataTable's built-in number key bindings for row jumping
        self.can_focus = True
        
        # Store the current DataFrame for editing
        self.current_df: Optional[pd.DataFrame] = None
        self.editing_cell = False
        self._columns_initialized = False
        
    def on_mount(self) -> None:
        """Initialize columns when mounted - will be updated when data loads."""
        self._columns_initialized = False
        logger.info("SimpleClusterView: Widget mounted, waiting for data")
    
    def on_key(self, event) -> None:
        """Override key handling for cell editing."""
        # Don't process keys if already editing - let them be handled by app buffer
        if self.editing_cell:
            return
            
        # Check for numerical keys that should trigger editing
        # Note: Textual maps '-' to 'subtract' and '.' to 'decimal' in some cases
        # So we check both event.key and event.character
        numerical_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-', 'subtract', 'decimal']
        
        # Check if it's a printable character we care about
        is_numeric_char = (event.character in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '-'] 
                          if event.character else False)
        
        if event.key in numerical_keys or is_numeric_char or event.key == "enter":
            # Stop DataTable from processing it
            event.stop()
            
            # Get current cell position
            if hasattr(self, 'cursor_coordinate'):
                row, col = self.cursor_coordinate
                
                # Get column name from column index
                if hasattr(self, '_column_names') and col < len(self._column_names):
                    column_name = self._column_names[col]
                    
                    # Check if this column is editable (VIEW or SHORTLIMIT)
                    if column_name in ['VIEW', 'SHORTLIMIT', 'SHORTLIMIT*']:
                        # Start editing - pass the initial character
                        # Use event.character for printable chars, otherwise check if it's a number key
                        if event.character and event.character in '0123456789.-':
                            initial_char = event.character
                        elif event.key in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                            initial_char = event.key
                        else:
                            initial_char = None
                        self.start_editing(row, col, column_name, initial_char)
                    else:
                        # Not an editable column
                        self.app.notify(f"Column {column_name} is not editable", severity="warning")
            return
        # Let other keys be handled normally by DataTable
    
    def load_data(self, df: pd.DataFrame) -> None:
        """Load dataframe into the table."""
        if df is None or df.empty:
            logger.warning("SimpleClusterView: No data to load")
            return
            
        try:
            # Initialize columns based on actual dataframe columns if not done yet
            if not self._columns_initialized:
                # Important columns to show first (if they exist)
                # Match actual column names from the Excel file
                priority_cols = ["CLUSTER", "SP", "CUID", "VIEW", "PREV (SEP25)", 
                                "PACTUAL", "PEXPECTED", "VIEWLG", "CSP95", "CSP80",
                                "LIMIT", "SOURCE", "SINK", "DIRECTION", "MON", "CONT"]
                
                # Get all columns from dataframe
                all_cols = list(df.columns)
                
                # Order columns: priority ones first (that exist), then others
                columns_to_add = []
                for col in priority_cols:
                    if col in all_cols:
                        columns_to_add.append(col)
                
                # Add any remaining columns not in priority list (limit to first 30 for display)
                for col in all_cols:
                    if col not in columns_to_add and len(columns_to_add) < 30:
                        columns_to_add.append(col)
                
                # Add columns to table with appropriate widths
                for col in columns_to_add:
                    # Set column widths based on column name
                    if "CUID" in col:
                        width = 20
                    elif col in ["CLUSTER", "SP", "VIEW", "PACTUAL", "PEXPECTED"]:
                        width = 10
                    elif col in ["SOURCE", "SINK"]:
                        width = 15
                    elif "PREV" in col:
                        width = 12
                    else:
                        width = 10  # Default width
                    
                    self.add_column(col, width=width)
                
                self._columns_initialized = True
                self._column_names = columns_to_add  # Store for later use
                logger.info(f"SimpleClusterView: Initialized {len(columns_to_add)} columns: {columns_to_add[:5]}...")
            
            # Clear only if we already have data
            if self._data_loaded and self.row_count > 0:
                self.clear()
            
            # Add rows - now we know the column structure
            # Show all rows, not just first 10
            for idx, row in df.iterrows():
                row_data = []
                # We added columns in the same order as stored in _column_names
                # So we iterate through those column names
                for col_name in self._column_names:
                    if col_name in row.index:
                        val = row[col_name]
                        if pd.isna(val):
                            row_data.append(Text(""))
                        else:
                            # Format based on data type
                            if isinstance(val, float):
                                # Get color for this column/value if applicable
                                text_val = f"{val:.2f}"
                                
                                # Check if this column should have color formatting
                                if col_name in self.column_type_map:
                                    column_type = self.column_type_map[col_name]
                                    color = self.formatter.get_color(column_type, val)
                                    
                                    # Convert hex color to Rich style
                                    if color and color != "#FFFFFF":
                                        # Create styled text with background color and dark text
                                        styled_text = Text(text_val)
                                        # Use black text on colored backgrounds for readability
                                        styled_text.stylize(f"black on {color}")
                                        row_data.append(styled_text)
                                    else:
                                        row_data.append(Text(text_val))
                                else:
                                    row_data.append(Text(text_val))
                            else:
                                row_data.append(Text(str(val)))
                    else:
                        row_data.append(Text(""))
                
                self.add_row(*row_data)
            
            self._data_loaded = True
            self.current_df = df  # Store DataFrame for editing
            logger.info(f"SimpleClusterView: Loaded {len(df)} rows with {len(self.columns)} columns")
            
        except Exception as e:
            logger.error(f"SimpleClusterView: Failed to load data: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start_editing(self, row: int, col: int, column_name: str, initial_char: str = None) -> None:
        """Start editing a cell."""
        if self.current_df is None:
            return
        
        # Set editing flag immediately
        self.editing_cell = True
        
        # Use the DataTable row position as DataFrame index
        df_row_index = row
        
        # Determine initial editor value
        # If the edit was triggered by typing a number, clear the existing content
        # and start with just that first character.
        if initial_char is not None:
            current_value = initial_char
        else:
            # Otherwise, use the current cell value as the starting point
            current_value = ""
            if df_row_index < len(self.current_df):
                df_row = self.current_df.iloc[df_row_index]
                if column_name in df_row.index:
                    val = df_row[column_name]
                    if pd.notna(val):
                        # Preserve how values are displayed in the table: avoid forcing 2 decimals
                        # to keep simple integers as-is (e.g., 4 instead of 4.00) when editing.
                        current_value = (
                            str(int(val)) if isinstance(val, float) and val.is_integer() else str(val)
                        )
        
        # Create and mount the editor overlay
        editor = CellEditor(
            initial_value=current_value,
            column_name=column_name,
            on_submit=lambda value: self.save_edit(row, col, column_name, value),
            on_cancel=self.cancel_edit,
            parent_view=self  # Pass reference to access keystroke buffer
        )
        
        # Mount the editor to the app
        self.app.mount(editor)
        
    def save_edit(self, row: int, col: int, column_name: str, value: str) -> None:
        """Save the edited value."""
        self.editing_cell = False
        
        # Use the DataTable row position as DataFrame index
        df_row_index = row
        
        if self.current_df is None or df_row_index >= len(self.current_df):
            return
        
        try:
            # Convert value to appropriate type
            if value.strip() == "":
                new_value = None
            else:
                new_value = float(value)
            
            # Get the actual DataFrame index for this row position
            actual_df_index = self.current_df.index[df_row_index]
            
            # Update the DataFrame at the correct row using the actual index
            self.current_df.at[actual_df_index, column_name] = new_value
            
            # Store current cursor position
            saved_cursor = self.cursor_coordinate
            
            # Reload the data to refresh the display with the updated value
            # This is simpler than trying to update individual cells
            self.load_data(self.current_df)
            
            # Restore cursor position to stay on same cell
            if saved_cursor:
                self.move_cursor(row=saved_cursor.row, column=saved_cursor.column)
            
            # Notify parent app to save to Excel
            if hasattr(self.app, 'on_cell_edit'):
                self.app.on_cell_edit(df_row_index, column_name, new_value)
            
            self.app.notify(f"Updated {column_name} to {value}", severity="information")
            
        except ValueError as e:
            self.app.notify(f"Invalid value: {e}", severity="error")
        finally:
            self.focus()
    
    def cancel_edit(self) -> None:
        """Cancel editing without saving."""
        self.editing_cell = False
        self.focus()
    
