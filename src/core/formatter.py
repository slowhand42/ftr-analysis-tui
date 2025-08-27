"""Color formatting logic based on Excel conditional formatting rules."""

from typing import Optional, Tuple
import math

from ..models import ColumnType


class ColorFormatter:
    """
    Calculates colors based on Excel conditional formatting rules.
    
    Color schemes:
    - Core columns (VIEW, PREV, etc.): White→Yellow→Red gradients
    - RECENT_DELTA: Blue→White→Red
    - Date grids: Value-based gradients  
    - LODF: Red→White→Green
    """
    
    # Color definitions (RGB hex)
    WHITE = "#FFFFFF"
    YELLOW = "#FFFF00"
    RED = "#FF0000"
    BLUE = "#0000FF"
    GREEN = "#00FF00"
    BLACK = "#000000"
    GREY = "#808080"
    
    def get_color(self, column_type: ColumnType, value: Optional[float]) -> str:
        """
        Get color for a cell based on column type and value.
        
        Args:
            column_type: Type of column
            value: Cell value (None for empty cells)
            
        Returns:
            Color string (hex RGB)
        """
        if value is None or math.isnan(value):
            return self.WHITE
        
        # Map column types to color methods
        if column_type in [ColumnType.VIEW, ColumnType.SP, ColumnType.PREV, 
                           ColumnType.PACTUAL, ColumnType.PEXPECTED, ColumnType.VIEWLG,
                           ColumnType.CSP95, ColumnType.CSP80, ColumnType.CSP50,
                           ColumnType.CSP20, ColumnType.CSP5]:
            return self._get_core_column_color(value)
        elif column_type == ColumnType.RECENT_DELTA:
            return self._get_recent_delta_color(value)
        elif column_type == ColumnType.DATE_COLUMN:
            return self._get_date_column_color(value)
        elif column_type == ColumnType.LODF_COLUMN:
            return self._get_lodf_color(value)
        elif column_type == ColumnType.FLOW:
            # No background color for FLOW, just bold text indicator
            return self.WHITE
        else:
            return self.WHITE
    
    def _get_core_column_color(self, value: float) -> str:
        """
        Get color for core columns (VIEW, PREV, etc.).
        
        Thresholds:
        - ≤ 0.5: White
        - 0.5 to 4th percentile: White→Yellow gradient  
        - 4th percentile to 20: Yellow→Red gradient
        - > 20: Red
        """
        if value <= 0.5:
            return self.WHITE
        elif value <= 1.0:  # Assuming 4th percentile around 1.0
            # White to Yellow gradient
            ratio = (value - 0.5) / 0.5
            return self._interpolate_color(self.WHITE, self.YELLOW, ratio)
        elif value <= 20:
            # Yellow to Red gradient
            ratio = (value - 1.0) / 19.0
            return self._interpolate_color(self.YELLOW, self.RED, ratio)
        else:
            return self.RED
    
    def _get_recent_delta_color(self, value: float) -> str:
        """
        Get color for RECENT_DELTA column.
        
        Thresholds:
        - -50: Blue
        - 0: White
        - +50: Red
        (Gradient between these points)
        """
        if value <= -50:
            return self.BLUE
        elif value < 0:
            # Blue to White gradient
            ratio = (value + 50) / 50
            return self._interpolate_color(self.BLUE, self.WHITE, ratio)
        elif value <= 50:
            # White to Red gradient
            ratio = value / 50
            return self._interpolate_color(self.WHITE, self.RED, ratio)
        else:
            return self.RED
    
    def _get_date_column_color(self, value: float) -> str:
        """
        Get color for date columns.
        
        SP rows (Parent):
        - 0: White
        - 0 to 10th percentile: White→Yellow
        - 10th percentile to 100: Yellow→Red
        - > 100: Red
        
        VIEW rows (Children):
        - 0: White
        - 0 to 150: White→Black gradient
        - > 150: Black
        """
        # For now, using SP row logic as default
        # In actual implementation, would need row context
        if value == 0:
            return self.WHITE
        elif value <= 10:  # Assuming 10th percentile
            ratio = value / 10
            return self._interpolate_color(self.WHITE, self.YELLOW, ratio)
        elif value <= 100:
            ratio = (value - 10) / 90
            return self._interpolate_color(self.YELLOW, self.RED, ratio)
        else:
            return self.RED
    
    def _get_lodf_color(self, value: float) -> str:
        """
        Get color for LODF columns.
        
        Thresholds:
        - -1.0: Red
        - 0.0: White  
        - +1.0: Green
        """
        if value <= -1.0:
            return self.RED
        elif value < 0:
            # Red to White gradient
            ratio = (value + 1.0)
            return self._interpolate_color(self.RED, self.WHITE, ratio)
        elif value <= 1.0:
            # White to Green gradient
            ratio = value
            return self._interpolate_color(self.WHITE, self.GREEN, ratio)
        else:
            return self.GREEN
    
    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """
        Linearly interpolate between two colors.
        
        Args:
            color1: Starting color (hex RGB)
            color2: Ending color (hex RGB)
            ratio: Interpolation ratio (0.0 to 1.0)
            
        Returns:
            Interpolated color (hex RGB)
        """
        # Ensure ratio is between 0 and 1
        ratio = max(0.0, min(1.0, ratio))
        
        # Parse hex colors
        r1, g1, b1 = self._hex_to_rgb(color1)
        r2, g2, b2 = self._hex_to_rgb(color2)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        # Convert back to hex
        return self._rgb_to_hex(r, g, b)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB tuple to hex color."""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def should_bold_flow(self, flow_value: float, max_hist: float) -> bool:
        """
        Determine if FLOW value should be displayed in bold.
        
        Args:
            flow_value: Current flow value
            max_hist: Historical maximum
            
        Returns:
            True if flow should be bold
        """
        return flow_value > max_hist if max_hist else False
    
    def get_error_color(self) -> str:
        """Get color for error cells."""
        return self.GREY